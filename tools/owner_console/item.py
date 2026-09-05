#!/usr/bin/env python
"""Write and read owner-console items from the research loop (Codex DM / Root).

This is the stable contract between the loop and the owner console: the loop never writes item
JSON by hand, it calls this script; the console never reads anything the loop did not write here.
Standard library only.

    # at the moment a delegated decision is recorded in the ledger
    python tools/owner_console/item.py add --direction flexible_skill_duration --kind decision \
        --title "next rung after E3" --context "..." \
        --option a "E2b: transfer c=0.25 to scenario 1" --option b "E4: random-duration events" \
        --recommended a --auto-applied a --dm-reason "..." \
        --evidence docs/research/candidates/flexible_skill_duration/FSD_E3_INTAKE_20260905.md \
        --ledger-row "docs/research/portfolio/audit/2026-09-05.md#L14" --ledger-kind selection

    # at every clean boundary: what the owner asked for that is not applied yet
    python tools/owner_console/item.py reviews            # human-readable
    python tools/owner_console/item.py reviews --json     # machine-readable
    python tools/owner_console/item.py mark-answered 20260905-fsd-003
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("owner_console_server", HERE / "server.py")
srv = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = srv
_spec.loader.exec_module(srv)

DEFAULT_OPTIONS = {
    "new-card": [("accept", "launch as carded"), ("reject", "do not launch"), ("revise", "revise before launch")],
    "brief": [("reading-agreed", "the reading stands"), ("reading-disputed", "re-read per the comment")],
    "second-recast": [("continue-low-priority", "continue at lowest sequencing priority"), ("park", "PARK the direction")],
    "portfolio": [("ratify", "ratify the proposal"), ("refuse", "refuse"), ("amend", "amend per the comment")],
}


def cmd_add(a) -> int:
    priority = srv.item_priority({"kind": a.kind, "tier": a.tier, "ledger_kind": a.ledger_kind})
    if priority > 2:
        print(f"skipped P{priority}: owner maintains P1/P2 only; cite the card/intake in the audit ledger")
        return 0
    options = [{"key": k, "label": label, "consequence": ""} for k, label in (a.option or [])]
    if not options and a.kind in DEFAULT_OPTIONS:
        options = [{"key": k, "label": l, "consequence": l} for k, l in DEFAULT_OPTIONS[a.kind]]
    for k, text in (a.consequence or []):
        for o in options:
            if o["key"] == k:
                o["consequence"] = text
    packet = None
    if a.packet:
        packet = json.loads(Path(a.packet).read_text(encoding="utf-8"))
    out = srv.new_item(a.root, a.direction, a.kind, a.title, options, recommended=a.recommended,
                       auto_applied=a.auto_applied, context=a.context or "", dm_reason=a.dm_reason or "",
                       evidence=a.evidence or [], tier=a.tier, ledger_row=a.ledger_row or "",
                       brief=a.brief or "", ledger_kind=a.ledger_kind or "", packet=packet)
    print(str(out.relative_to(a.root)).replace("\\", "/"))
    return 0


def cmd_reviews(a) -> int:
    rows = srv.pending_instructions(a.root, days=a.days)
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    if not rows:
        print("no unapplied owner instructions")
        return 0
    for r in rows:
        print(f"{r['id']} · {r['direction']} · {r['kind']} · {r['title']}")
        print(f"  owner: {r['choice']}" + (f" · comment: {r['comment']}" if r["comment"] else ""))
        print(f"  instruction: {r['instruction']}")
    return 0


def cmd_mark(a) -> int:
    for item_id in a.ids:
        p = srv.mark_answered(a.root, item_id)
        print(str(p.relative_to(a.root)).replace("\\", "/"))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=srv.DEFAULT_ROOT)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("add", help="write one item")
    s.add_argument("--direction", required=True)
    s.add_argument("--kind", required=True, choices=srv.KINDS)
    s.add_argument("--title", required=True)
    s.add_argument("--tier", default="object", choices=("object", "direction", "portfolio"))
    s.add_argument("--context", default="")
    s.add_argument("--option", nargs=2, action="append", metavar=("KEY", "LABEL"))
    s.add_argument("--consequence", nargs=2, action="append", metavar=("KEY", "TEXT"))
    s.add_argument("--recommended")
    s.add_argument("--auto-applied", dest="auto_applied")
    s.add_argument("--dm-reason", dest="dm_reason", default="")
    s.add_argument("--evidence", action="append")
    s.add_argument("--ledger-row", dest="ledger_row", default="")
    s.add_argument("--ledger-kind", dest="ledger_kind", default="", choices=("", "technical", "selection"))
    s.add_argument("--brief", default="")
    s.add_argument("--packet", help="JSON file with the decision packet (required for portfolio, "
                                    "second-recast, critic-dissent, close-call, new-card and any "
                                    "direction/portfolio-tier item; see owner/README.md)")
    s.set_defaults(fn=cmd_add)

    r = sub.add_parser("reviews", help="owner instructions not yet applied")
    r.add_argument("--days", type=int, default=2)
    r.add_argument("--json", action="store_true")
    r.set_defaults(fn=cmd_reviews)

    m = sub.add_parser("mark-answered", help="record that the loop applied the owner's instruction")
    m.add_argument("ids", nargs="+")
    m.set_defaults(fn=cmd_mark)

    a = ap.parse_args(argv)
    try:
        return a.fn(a)
    except (ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
