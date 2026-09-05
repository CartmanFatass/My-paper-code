#!/usr/bin/env python
"""HMASD owner console.

A local grading page for the owner surfaces (`docs/research/portfolio/owner/`). The Codex loop
writes one item JSON per thing that needs the owner's eye; this page renders them as cards; the
owner picks an option and comments; the console writes a reply file next to the item, regenerates
`reviews/<date>.md` (the document the loop reads), and commits both by pathspec.

Standard library only. Binds 127.0.0.1. Nothing in the research loop depends on this process.

    python tools/owner_console/server.py                 # serve on http://127.0.0.1:8765
    python tools/owner_console/server.py seed-ledger 2026-09-04   # one-off: ledger rows -> items
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parents[1]
LOCK = threading.Lock()

OWNER_REL = Path("docs/research/portfolio/owner")
AUDIT_REL = Path("docs/research/portfolio/audit")
PORTFOLIO_REL = Path("docs/research/portfolio/PORTFOLIO.md")
DOC_SUFFIXES = {".md", ".json", ".txt", ".toml", ".patch"}

KINDS = ("decision", "new-card", "prediction", "brief", "critic-dissent", "close-call",
         "second-recast", "portfolio")

# direction id -> script prefix (docs/research/RESEARCH_MAP.md); used for item ids
PREFIX = {
    "active_post_churn_population_flow_identification": "apfi", "acvc": "acvc",
    "capability_bound_semantic_currentness": "cbsc", "commitment_residual_triggered_options": "crto",
    "degraded_incumbent_shadow_handover": "dish", "ec4g_r1": "ec4g", "eociv_lite": "eociv",
    "expressibility_gated_renewal_credit_relay": "egrcr",
    "finite_resource_relational_inductive_efficiency": "frrie", "flexible_skill_duration": "fsd",
    "metric_ground_transport_allocation": "mgtap", "orbit_shadow_read": "orbit",
    "recct_lite": "recct", "roster_consistent_latent_exploration": "rcle", "scope_1s": "scope1s",
    "semigroup_consistent_duration_model_policy": "scdmp", "ucope": "ucope",
    "vap_folr_core": "folr", "variable_n_fleet_churn": "vnfc", "vsp_02": "vsp02",
    "vsp_03": "vsp03", "vsp_c1": "vspc1", "portfolio": "root",
}


# ----------------------------------------------------------------------------- markdown tables

def parse_md_table(text: str) -> list[dict]:
    """Return the rows of the first markdown table in `text` as dicts keyed by header."""
    rows, header = [], None
    for line in text.splitlines():
        s = line.strip()
        if not (s.startswith("|") and s.endswith("|")):
            if header is not None and rows:
                break
            continue
        cells = [c.strip() for c in _split_row(s)]
        if header is None:
            header = cells
            continue
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            continue
        if len(cells) < len(header):
            cells += [""] * (len(header) - len(cells))
        rows.append(dict(zip(header, cells[: len(header)])))
    return rows


def _split_row(s: str) -> list[str]:
    s = s[1:-1].replace("\\|", "\x00")
    return [c.replace("\x00", "|") for c in s.split("|")]


# ----------------------------------------------------------------------------- items and replies

# grading priority buckets: 1 = needs the owner's ruling, 4 = read when convenient
KIND_PRIORITY = {"portfolio": 1, "second-recast": 1, "critic-dissent": 2, "close-call": 2,
                 "new-card": 2, "decision": 3, "prediction": 3, "brief": 4}
DIR_PRIORITY_RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def owner_dir(root: Path) -> Path:
    return root / OWNER_REL


# kinds that ask the owner to rule (P1/P2) must carry a decision packet, not a one-line context
PACKET_KINDS = ("portfolio", "second-recast", "critic-dissent", "close-call", "new-card")
PACKET_REQUIRED = ("question", "changes_if_approved", "if_refused", "evidence_for", "cost")
UNIVERSAL_CHOICES = ("agree", "other", "needs-context")


def needs_packet(item: dict) -> bool:
    return item.get("kind") in PACKET_KINDS or item.get("tier") in ("direction", "portfolio")


def packet_problems(item: dict) -> list[str]:
    """Why a decision-bearing item cannot be ruled on; empty when the packet is complete."""
    if not needs_packet(item):
        return []
    pk = item.get("packet") or {}
    probs = [f"packet.{k} missing" for k in PACKET_REQUIRED if not pk.get(k)]
    ev = pk.get("evidence_for") or []
    if ev and not all(isinstance(e, dict) and e.get("path") and e.get("quote") for e in ev):
        probs.append("every evidence_for entry needs path and quote")
    if isinstance(pk.get("cost"), dict) and not pk["cost"].get("reversibility"):
        probs.append("packet.cost.reversibility missing")
    for o in item.get("options", []):
        if not (o.get("consequence") or "").strip():
            probs.append(f"option ({o.get('key')}) has no consequence")
    return probs


def item_priority(item: dict) -> int:
    p = KIND_PRIORITY.get(item.get("kind"), 3)
    if item.get("kind") == "decision":
        if item.get("tier") in ("direction", "portfolio"):
            p = 2
        elif item.get("ledger_kind") == "technical":
            p = 4
    return p


def new_item(root: Path, direction: str, kind: str, title: str, options: list[dict], *,
             recommended: str | None = None, auto_applied: str | None = None, context: str = "",
             dm_reason: str = "", evidence: list[str] | None = None, tier: str = "object",
             ledger_row: str = "", brief: str = "", ledger_kind: str = "", day: str | None = None,
             packet: dict | None = None) -> Path:
    """Write one validated item; the id is <YYYYMMDD>-<prefix>-<nnn> with the next free nnn.

    Decision-bearing kinds (PACKET_KINDS, or any direction/portfolio-tier item) are refused
    without a complete decision packet: the owner cannot rule on a one-line context.
    """
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    probe = {"kind": kind, "tier": tier, "options": options, "packet": packet}
    probs = packet_problems(probe)
    if probs:
        raise ValueError("decision packet incomplete: " + "; ".join(probs))
    if not title.strip():
        raise ValueError("title is required")
    if not options:
        raise ValueError("at least one option is required")
    keys = [o.get("key") for o in options]
    if len(set(keys)) != len(keys) or any(not k for k in keys):
        raise ValueError("option keys must be unique and non-empty")
    for name, val in (("recommended", recommended), ("auto_applied", auto_applied)):
        if val is not None and val not in keys:
            raise ValueError(f"{name}={val!r} is not an option key")
    day = day or dt.date.today().isoformat()
    prefix = PREFIX.get(direction) or re.sub(r"[^a-z0-9]", "", direction.lower())[:8] or "x"
    day_dir = owner_dir(root) / "inbox" / day
    n = 1 + len(list(day_dir.glob(f"{day.replace('-', '')}-{prefix}-*.json"))) if day_dir.exists() else 1
    existing = {p.stem for p in day_dir.glob("*.json")} if day_dir.exists() else set()
    while f"{day.replace('-', '')}-{prefix}-{n:03d}" in existing:
        n += 1
    item_id = f"{day.replace('-', '')}-{prefix}-{n:03d}"
    item = {
        "id": item_id,
        "created": dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds"),
        "direction": direction, "tier": tier, "kind": kind, "title": title.strip(),
        "context": context, "options": options, "recommended": recommended,
        "auto_applied": auto_applied, "dm_reason": dm_reason, "evidence": evidence or [],
        "ledger_row": ledger_row, "brief": brief, "ledger_kind": ledger_kind, "status": "open",
        "packet": packet or None,
        "starred": tier in ("direction", "portfolio") or kind in ("second-recast", "critic-dissent", "close-call"),
    }
    out = day_dir / f"{item_id}.json"
    _atomic_write(out, json.dumps(item, ensure_ascii=False, indent=2) + "\n")
    return out


def record_trace(root: Path, item_id: str, *, authority: str, source: str, record: str,
                 state: str, summary: str, auto_applied: str | None = None,
                 correction: str = "") -> Path:
    """Annotate actual execution without manufacturing or replacing an owner reply."""
    p = item_path(root, item_id)
    if p is None:
        raise FileNotFoundError(f"no item {item_id}")
    item = json.loads(p.read_text(encoding="utf-8"))
    if item_priority(item) > 2:
        raise ValueError("P3/P4 maintenance remains retired")
    if auto_applied is not None:
        if state != "applied" or auto_applied not in {o["key"] for o in item["options"]}:
            raise ValueError("auto_applied requires an applied option from this item")
        item["auto_applied"] = auto_applied
    trace = {"at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
             "authority": authority, "source": source, "record": record,
             "state": state, "summary": summary}
    if correction:
        trace["correction"] = correction
        item["approval_correction"] = correction
        reply_path = p.with_suffix(".reply.json")
        if reply_path.exists():
            item["corrected_reply_at"] = json.loads(reply_path.read_text(encoding="utf-8")).get("answered_at")
    item.setdefault("execution_history", []).append(trace)
    item["starred"] = True
    _atomic_write(p, json.dumps(item, ensure_ascii=False, indent=2) + "\n")
    return p


def mark_answered(root: Path, item_id: str) -> Path:
    p = item_path(root, item_id)
    if p is None:
        raise FileNotFoundError(f"no item {item_id}")
    item = json.loads(p.read_text(encoding="utf-8"))
    item["status"] = "answered"
    _atomic_write(p, json.dumps(item, ensure_ascii=False, indent=2) + "\n")
    return p


def pending_instructions(root: Path, days: int = 2) -> list[dict]:
    """Replies whose item is not yet marked answered in the item file: what the loop must apply."""
    out = []
    for item in load_items(root, days=days):
        reply = item.get("reply")
        if not reply:
            continue
        raw = json.loads((root / item["path"]).read_text(encoding="utf-8"))
        if raw.get("status") == "answered":
            continue
        out.append({"id": item["id"], "direction": item.get("direction"), "kind": item.get("kind"),
                    "title": item.get("title"), "choice": reply.get("choice"), "comment": reply.get("comment", ""),
                    "instruction": instruction_for(item, reply), "answered_at": reply.get("answered_at")})
    return out


def item_path(root: Path, item_id: str) -> Path | None:
    for p in (owner_dir(root) / "inbox").glob(f"*/{item_id}.json"):
        return p
    return None


def load_items(root: Path, days: int | None = 7) -> list[dict]:
    inbox = owner_dir(root) / "inbox"
    if not inbox.exists():
        return []
    cutoff = (dt.date.today() - dt.timedelta(days=days)).isoformat() if days is not None else ""
    items = []
    for day_dir in sorted(inbox.iterdir(), reverse=True):
        if not day_dir.is_dir() or day_dir.name < cutoff:
            continue
        for p in sorted(day_dir.glob("*.json")):
            if p.name.endswith(".reply.json"):
                continue
            try:
                item = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                item = {"id": p.stem, "title": f"unreadable item: {exc}", "options": []}
            item.setdefault("id", p.stem)
            item.setdefault("kind", "decision")
            item.setdefault("options", [])
            item["path"] = str(p.relative_to(root)).replace(os.sep, "/")
            item["day"] = day_dir.name
            rp = p.with_suffix(".reply.json")
            if rp.exists():
                try:
                    item["reply"] = json.loads(rp.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    item["reply"] = None
            item["status"] = "answered" if item.get("reply") else item.get("status", "open")
            item["reply_attribution_corrected"] = bool(item.get("corrected_reply_at") and
                item["corrected_reply_at"] == (item.get("reply") or {}).get("answered_at"))
            items.append(item)
    return items


def write_reply(root: Path, item_id: str, choice: str, comment: str) -> dict:
    p = item_path(root, item_id)
    if p is None:
        raise FileNotFoundError(f"no item {item_id}")
    item = json.loads(p.read_text(encoding="utf-8"))
    keys = {o.get("key") for o in item.get("options", [])} | set(UNIVERSAL_CHOICES)
    if choice not in keys:
        raise ValueError(f"choice {choice!r} is not an option of {item_id}")
    now = dt.datetime.now(dt.timezone.utc).astimezone()
    reply = {
        "id": item_id,
        "choice": choice,
        "comment": comment.strip(),
        "answered_at": now.isoformat(timespec="seconds"),
        "recommended": item.get("recommended"),
        "auto_applied": item.get("auto_applied"),
    }
    rp = p.with_suffix(".reply.json")
    _atomic_write(rp, json.dumps(reply, ensure_ascii=False, indent=2) + "\n")
    if item.get("status") == "answered":
        item["status"] = "open"
        _atomic_write(p, json.dumps(item, ensure_ascii=False, indent=2) + "\n")
    review = render_review(root, now.date().isoformat())
    return {"reply": str(rp.relative_to(root)).replace(os.sep, "/"),
            "item": str(p.relative_to(root)).replace(os.sep, "/"),
            "review": str(review.relative_to(root)).replace(os.sep, "/")}


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


# ----------------------------------------------------------------------------- review document

def instruction_for(item: dict, reply: dict) -> str:
    choice, auto = reply.get("choice"), item.get("auto_applied")
    kind = item.get("kind", "decision")
    if choice == "needs-context":
        return ("owner cannot rule on this context; re-file as a new item with a complete decision packet "
                "(owner/README.md, packet section), then mark this one answered")
    if choice == "agree":
        return "none (seen; delegated decision stands)" if auto else "none (seen)"
    if kind == "decision" or kind in ("critic-dissent", "close-call"):
        if auto and choice == auto:
            return f"none (owner confirms the delegated ({auto}))"
        if auto:
            return f"apply ({choice}) at the next clean boundary; supersede the delegated ({auto})"
        return f"apply ({choice}) at the next clean boundary"
    if kind == "new-card":
        return {"accept": "launch as carded", "reject": "do not launch; record the owner's reason",
                "revise": "revise the card per the comment before launch"}.get(choice, f"apply ({choice})")
    if kind == "prediction":
        return f"record the owner's prediction ({choice}); score it at intake"
    if kind == "brief":
        return "none" if choice == "reading-agreed" else "re-read the result per the comment; answer in the next intake"
    if kind == "second-recast":
        return "PARK at the next clean boundary (Portfolio record required)" if choice == "park" else "continue at lowest sequencing priority"
    if kind == "portfolio":
        return {"ratify": "ratified; integrate into PORTFOLIO.md", "refuse": "refused; do not apply",
                "amend": "amend per the comment and resubmit"}.get(choice, f"apply ({choice})")
    return f"apply ({choice})"


def render_review(root: Path, date: str) -> Path:
    """Regenerate reviews/<date>.md from every reply answered on `date`."""
    entries = []
    for item in load_items(root, days=None):
        reply = item.get("reply")
        if not reply or not str(reply.get("answered_at", "")).startswith(date):
            continue
        entries.append((reply["answered_at"], item, reply))
    entries.sort(key=lambda e: e[0])
    lines = [f"# Owner review — {date}", "",
             "Written by the owner console from the reply files under `inbox/`. The loop reads this "
             "file at every clean boundary and applies each `instruction` line; `agree` means seen.", ""]
    for _, item, reply in entries:
        labels = {o.get("key"): o.get("label", "") for o in item.get("options", [])}
        ch = reply["choice"]
        ch_txt = ch if ch in UNIVERSAL_CHOICES else f"({ch}) {labels.get(ch, '')}".strip()
        lines.append(f"## {item['id']} · {item.get('direction', '?')} · {item.get('kind')} · {item.get('title', '')}")
        meta = []
        if item.get("recommended"):
            meta.append(f"recommended: ({item['recommended']})")
        if item.get("auto_applied"):
            meta.append(f"auto-applied: ({item['auto_applied']})")
        meta.append(f"**owner: {ch_txt}**")
        lines.append("- " + " · ".join(meta))
        if reply.get("comment"):
            lines.append(f"- comment: {reply['comment']}")
        if item.get("reply_attribution_corrected"):
            lines.append(f"- authorization correction: {item['approval_correction']}")
            lines.append("- instruction: historical reply attribution superseded; consult the execution record")
            for trace in item.get("execution_history", []):
                lines.append(f"- execution record: `{trace['record']}` · {trace['authority']} · {trace['at']}")
        else:
            lines.append(f"- instruction: {instruction_for(item, reply)}")
        for ev in item.get("evidence", []) or []:
            lines.append(f"- evidence: `{ev}`")
        lines.append(f"- item: `{item['path']}` · answered {reply['answered_at']}")
        lines.append("")
    out = owner_dir(root) / "reviews" / f"{date}.md"
    _atomic_write(out, "\n".join(lines).rstrip() + "\n")
    return out


def export_selected(root: Path, ids: list[str], slug: str) -> Path:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", slug).strip("-") or "selection"
    date = dt.date.today().isoformat()
    wanted = set(ids)
    lines = [f"# Owner review (selection) — {date} — {slug}", ""]
    for item in load_items(root, days=None):
        if item["id"] not in wanted:
            continue
        reply = item.get("reply") or {"choice": "unanswered", "comment": "", "answered_at": ""}
        lines.append(f"## {item['id']} · {item.get('direction', '?')} · {item.get('kind')} · {item.get('title', '')}")
        lines.append(f"- context: {item.get('context', '')}")
        for o in item.get("options", []):
            mark = " ★" if o.get("key") == item.get("recommended") else ""
            lines.append(f"- ({o.get('key')}) {o.get('label', '')}{mark}")
        lines.append(f"- **owner: {reply['choice']}** {reply.get('comment', '')}".rstrip())
        if item.get("reply_attribution_corrected"):
            lines.append(f"- authorization correction: {item['approval_correction']}")
        elif reply.get("answered_at"):
            lines.append(f"- instruction: {instruction_for(item, reply)}")
        for trace in item.get("execution_history", []):
            lines.append(f"- execution: {trace['state']} · {trace['authority']} · {trace['at']} · {trace['summary']}")
            lines.append(f"- source: `{trace['source']}`; actual change record: `{trace['record']}`")
        lines.append("")
    out = owner_dir(root) / "reviews" / f"{date}_{slug}.md"
    _atomic_write(out, "\n".join(lines).rstrip() + "\n")
    return out


# ----------------------------------------------------------------------------- other sources

def parse_portfolio(root: Path) -> dict:
    p = root / PORTFOLIO_REL
    if not p.exists():
        return {"updated": "", "rows": []}
    text = p.read_text(encoding="utf-8")
    m = re.search(r"^Updated at: (.+)$", text, re.M)
    return {"updated": m.group(1).strip() if m else "", "rows": parse_md_table(text)}


def investment_wave(root: Path) -> dict[str, int]:
    """Direction -> rank in the '## First investment wave' numbered list of PORTFOLIO.md."""
    p = root / PORTFOLIO_REL
    if not p.exists():
        return {}
    text = p.read_text(encoding="utf-8")
    m = re.search(r"^## First investment wave\s*$(.*?)^(?:##|###) ", text, re.M | re.S)
    if not m:
        return {}
    return {d: int(n) for n, d in re.findall(r"^\s*(\d+)\.\s+`([^`]+)`", m.group(1), re.M)}


def enrich_items(root: Path, items: list[dict]) -> list[dict]:
    prio = {r.get("Direction"): r.get("Priority", "") for r in parse_portfolio(root)["rows"]}
    for it in items:
        it["priority"] = item_priority(it)
        it["code"] = PREFIX.get(it.get("direction", ""), (it.get("direction") or "?")[:6])
        it["dir_priority"] = prio.get(it.get("direction"), "")
        it["context_problems"] = packet_problems(it)
    return items


def review_items(root: Path, days: int = 7) -> list[dict]:
    """Owner-directed P1/P2 queue; historical items and replies stay readable."""
    return [it for it in load_items(root, days=days) if item_priority(it) <= 2]


def starred_items(root: Path) -> list[dict]:
    return [it for it in load_items(root, days=None) if it.get("starred") and item_priority(it) <= 2]


def active_board(root: Path) -> dict:
    """ACTIVE directions with item statistics, for the board page."""
    port = parse_portfolio(root)
    wave = investment_wave(root)
    items = review_items(root, days=30)
    briefs = list_briefs(root)
    stats: dict[str, dict] = {}
    for it in items:
        s = stats.setdefault(it.get("direction"), {"open": 0, "answered": 0, "p1": 0, "last": ""})
        if it["status"] == "answered":
            s["answered"] += 1
        else:
            s["open"] += 1
            if item_priority(it) == 1:
                s["p1"] += 1
        s["last"] = max(s["last"], it.get("created") or it.get("day") or "")
    last_brief = {}
    for b in briefs:
        last_brief.setdefault(b["direction"], b)
    rows = []
    for r in port["rows"]:
        d = r.get("Direction", "")
        s = stats.get(d, {"open": 0, "answered": 0, "p1": 0, "last": ""})
        rows.append({
            "direction": d, "code": PREFIX.get(d, d[:6]), "lifecycle": r.get("Lifecycle", ""),
            "priority": r.get("Priority", ""), "updated": r.get("Updated at", ""),
            "reason": r.get("Reason/condition", ""), "wave": wave.get(d),
            "open": s["open"], "answered": s["answered"], "p1": s["p1"], "last_item": s["last"],
            "brief": (last_brief.get(d) or {}).get("path"),
            "direction_doc": f"docs/research/candidates/{d}/DIRECTION.md",
        })
    rows.sort(key=lambda r: (0 if r["lifecycle"] == "ACTIVE" else 1,
                             DIR_PRIORITY_RANK.get(r["priority"], 9), r["wave"] or 99,
                             -r["open"], r["updated"]), reverse=False)
    today = dt.date.today().isoformat()
    return {"updated": port["updated"], "rows": rows,
            "totals": {"directions": len(rows), "active": sum(r["lifecycle"] == "ACTIVE" for r in rows),
                       "parked": sum(r["lifecycle"] == "PARKED" for r in rows),
                       "open": sum(r["open"] for r in rows),
                       "answered_today": sum(1 for it in items if it.get("reply") and str(it["reply"].get("answered_at", "")).startswith(today))}}


def list_briefs(root: Path) -> list[dict]:
    out = []
    bdir = owner_dir(root) / "briefs"
    if not bdir.exists():
        return out
    for p in sorted(bdir.glob("*/*.md"), key=lambda q: q.stat().st_mtime, reverse=True):
        out.append({"direction": p.parent.name, "name": p.stem,
                    "path": str(p.relative_to(root)).replace(os.sep, "/"),
                    "mtime": dt.datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="minutes")})
    return out


def list_reviews(root: Path) -> list[str]:
    rdir = owner_dir(root) / "reviews"
    return sorted((str(p.relative_to(root)).replace(os.sep, "/") for p in rdir.glob("*.md")), reverse=True) if rdir.exists() else []


def read_doc(root: Path, rel: str) -> str:
    rel = rel.split("#", 1)[0]
    target = (root / rel).resolve()
    if root.resolve() not in target.parents or target.suffix.lower() not in DOC_SUFFIXES:
        raise PermissionError(f"refused: {rel}")
    if not target.is_file():
        raise FileNotFoundError(rel)
    return target.read_text(encoding="utf-8", errors="replace")


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")


def git_commit(root: Path, paths: list[str], message: str) -> dict:
    with LOCK:
        add = git(root, "add", "--", *paths)
        if add.returncode:
            return {"ok": False, "step": "add", "err": add.stderr}
        cm = git(root, "commit", "-q", "-m", message, "-m", "scope: none", "--", *paths)
        if cm.returncode and "nothing to commit" not in (cm.stdout + cm.stderr):
            return {"ok": False, "step": "commit", "err": cm.stderr or cm.stdout}
        sha = git(root, "rev-parse", "--short", "HEAD").stdout.strip()
        return {"ok": True, "sha": sha}


def git_status(root: Path) -> dict:
    log = git(root, "log", "--oneline", "-n", "12").stdout.splitlines()
    ahead = git(root, "rev-list", "--count", "@{u}..HEAD").stdout.strip()
    return {"log": log, "ahead": int(ahead) if ahead.isdigit() else None,
            "branch": git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()}


# ----------------------------------------------------------------------------- ledger seeding

def seed_from_ledger(root: Path, date: str) -> list[Path]:
    """One-off migration: every row of audit/<date>.md becomes a `decision` item, auto-applied."""
    src = root / AUDIT_REL / f"{date}.md"
    rows = parse_md_table(src.read_text(encoding="utf-8"))
    counters: dict[str, int] = {}
    written = []
    for row in rows:
        direction = row.get("direction", "").strip("` ")
        prefix = PREFIX.get(direction, re.sub(r"[^a-z0-9]", "", direction)[:8] or "x")
        counters[prefix] = counters.get(prefix, 0) + 1
        item_id = f"{date.replace('-', '')}-{prefix}-{counters[prefix]:03d}"
        options = _split_options(row.get("options", ""))
        chosen = row.get("chosen option", "")
        auto = _match_option(options, chosen)
        if re.fullmatch(r"\(([a-z])\)\s*", chosen) and auto:
            chosen = next((f"({auto}) {o['label']}" for o in options if o["key"] == auto), chosen)
        evidence = [e.strip("` ") for e in re.findall(r"`([^`]+)`", row.get("evidence path", ""))] or \
                   ([row.get("evidence path", "").strip("` ")] if row.get("evidence path") else [])
        t = row.get("time", "").strip()
        created = t if re.match(r"\d{4}-\d{2}-\d{2}", t) else f"{date} {t}".strip()
        item = {
            "id": item_id, "created": created,
            "direction": direction, "tier": row.get("tier", "object"), "kind": "decision",
            "title": (chosen[:90] + "…") if len(chosen) > 90 else chosen,
            "context": f"Delegated decision recorded in the audit ledger ({date}, {row.get('time', '')}). "
                       f"Provenance: {row.get('provenance label', '')}. Reversible: {row.get('reversible', '')}.",
            "options": options, "recommended": auto, "auto_applied": auto,
            "dm_reason": "", "evidence": evidence,
            "ledger_row": str(AUDIT_REL / f"{date}.md").replace(os.sep, "/"),
            "status": "open", "source": "seed-ledger",
        }
        out = owner_dir(root) / "inbox" / date / f"{item_id}.json"
        if out.exists():
            continue
        _atomic_write(out, json.dumps(item, ensure_ascii=False, indent=2) + "\n")
        written.append(out)
    return written


def _split_options(text: str) -> list[dict]:
    parts = [p.strip() for p in re.split(r";\s*", text) if p.strip()]
    options = []
    for i, part in enumerate(parts):
        m = re.match(r"\(([a-z])\)\s*(.*)", part)
        key = m.group(1) if m else chr(ord("a") + i)
        label = m.group(2) if m else part
        options.append({"key": key, "label": label, "consequence": ""})
    return options


def _match_option(options: list[dict], chosen: str) -> str | None:
    m = re.match(r"\(([a-z])\)", chosen.strip())
    if m and any(o["key"] == m.group(1) for o in options):
        return m.group(1)
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
    c = norm(chosen)
    best, score = None, 0
    for o in options:
        l = norm(o["label"])
        if not l:
            continue
        s = len(os.path.commonprefix([l, c]))
        if l in c or c in l:
            s = max(s, min(len(l), len(c)))
        if s > score:
            best, score = o["key"], s
    return best if score >= 6 else None


# ----------------------------------------------------------------------------- http

class Handler(BaseHTTPRequestHandler):
    root: Path = DEFAULT_ROOT

    def log_message(self, fmt, *args):  # quieter console
        if "/api/" not in (args[0] if args else ""):
            return

    def _send(self, code: int, body: bytes, ctype: str = "application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(url.query)
        try:
            if url.path in ("/", "/index.html"):
                self._send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
            elif url.path == "/api/items":
                items = enrich_items(self.root, review_items(self.root, int(q.get("days", ["7"])[0])))
                self._json({"items": items, "today": dt.date.today().isoformat()})
            elif url.path == "/api/active":
                self._json(active_board(self.root))
            elif url.path == "/api/starred":
                self._json({"items": enrich_items(self.root, starred_items(self.root))})
            elif url.path == "/api/portfolio":
                self._json(parse_portfolio(self.root))
            elif url.path == "/api/briefs":
                self._json({"briefs": list_briefs(self.root)})
            elif url.path == "/api/reviews":
                self._json({"reviews": list_reviews(self.root)})
            elif url.path == "/api/git":
                self._json(git_status(self.root))
            elif url.path == "/api/doc":
                self._json({"path": q["path"][0], "text": read_doc(self.root, q["path"][0])})
            else:
                self._json({"error": "not found"}, 404)
        except (PermissionError, FileNotFoundError, KeyError, ValueError) as exc:
            self._json({"error": str(exc)}, 400)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
            if self.path == "/api/reply":
                paths = write_reply(self.root, body["id"], body.get("choice", "agree"), body.get("comment", ""))
                res = git_commit(self.root, [paths["item"], paths["reply"], paths["review"]],
                                 f"owner: review {body['id']} ({body.get('choice', 'agree')})")
                self._json({"ok": res.get("ok", False), **paths, "git": res})
            elif self.path == "/api/export":
                out = export_selected(self.root, body.get("ids", []), body.get("slug", "selection"))
                rel = str(out.relative_to(self.root)).replace(os.sep, "/")
                res = git_commit(self.root, [rel], f"owner: review selection {out.stem}")
                self._json({"ok": res.get("ok", False), "path": rel, "git": res})
            elif self.path == "/api/push":
                with LOCK:
                    r = git(self.root, "-c", "push.default=upstream", "push")
                self._json({"ok": r.returncode == 0, "out": (r.stdout + r.stderr)[-2000:]})
            else:
                self._json({"error": "not found"}, 404)
        except (PermissionError, FileNotFoundError, KeyError, ValueError) as exc:
            self._json({"error": str(exc)}, 400)


def serve(root: Path, host: str, port: int) -> None:
    Handler.root = root
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"owner console: http://{host}:{port}/  (repo {root})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="repository root")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("seed-ledger", help="turn one day's audit ledger rows into inbox items")
    s.add_argument("date")
    r = sub.add_parser("render-review", help="regenerate reviews/<date>.md")
    r.add_argument("date")
    a = ap.parse_args(argv)
    if a.cmd == "seed-ledger":
        print("skipped: bulk P3/P4 ledger seeding retired by owner; use item.py for P1/P2")
        return 0
    if a.cmd == "render-review":
        print(render_review(a.root, a.date).relative_to(a.root))
        return 0
    serve(a.root, a.host, a.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
