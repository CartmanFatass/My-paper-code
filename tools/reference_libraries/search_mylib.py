#!/usr/bin/env python3
"""AND-terms search over the My-lib LLM index (catalog + hints). Stdlib only.

Every term must occur (case-insensitive substring) in a paper's title, abstract, ids, venue or
hint fields. Prints ``id | venue-year | title | path | one-line hint``; ``--json`` prints rows.
Hints locate papers; they are not evidence. Open the PDF before relying on anything.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_OUT = Path("/mnt/c/Projects/My-lib/.local-llm-index")
# ``hmasd_relevance_reason`` is excluded: it names the HMASD themes when explaining why a paper is
# NOT relevant ("no link to hierarchical multi-agent skills or UAV planning"), which would make
# queries such as "hierarchical skill" match most of the corpus.
TEXT_FIELDS = ("id", "venue", "year", "title", "arxiv_id", "abstract", "problem_setting", "method_summary",
               "key_mechanism", "marl_setting", "one_line_hint")
LIST_FIELDS = ("mechanism_keywords", "topics", "authors")


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_index(out: Path) -> List[Dict[str, Any]]:
    """Catalog rows, each merged with its hint when one exists."""
    catalog = read_jsonl(out / "catalog.jsonl")
    hints: Dict[str, Dict[str, Any]] = {}
    merged = read_jsonl(out / "hints.jsonl")
    if merged:
        hints = {r["id"]: r for r in merged}
    elif (out / "hints").exists():
        for path in sorted((out / "hints").glob("*.json")):
            if path.name.endswith(".error.json"):
                continue
            rec = json.loads(path.read_text(encoding="utf-8"))
            hints[rec["id"]] = rec.get("hint", {})
    rows = []
    for c in catalog:
        row = dict(c)
        h = hints.get(c["id"])
        if h:
            for k, v in h.items():
                if k not in row or row[k] in (None, ""):
                    row[k] = v
        row["has_hint"] = bool(h)
        rows.append(row)
    return rows


def haystack(row: Dict[str, Any]) -> str:
    parts = [str(row.get(k) or "") for k in TEXT_FIELDS]
    for k in LIST_FIELDS:
        v = row.get(k)
        if isinstance(v, list):
            parts.extend(str(x) for x in v)
    return "\n".join(parts).lower()


def search(rows: List[Dict[str, Any]], terms: List[str], min_relevance: Optional[int] = None,
           topics: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    needles = [t.lower() for t in terms if t.strip()]
    hits = []
    for row in rows:
        if min_relevance is not None and (row.get("hmasd_relevance") is None or row["hmasd_relevance"] < min_relevance):
            continue
        if topics and not all(t in (row.get("topics") or []) for t in topics):
            continue
        text = haystack(row)
        if all(n in text for n in needles):
            hits.append(row)
    hits.sort(key=lambda r: (-(r.get("hmasd_relevance") if r.get("hmasd_relevance") is not None else -1), str(r["id"])))
    return hits


def format_row(row: Dict[str, Any]) -> str:
    vy = f"{row.get('venue')}-{row.get('year')}" if row.get("venue") else "loose"
    rel = row.get("hmasd_relevance")
    hint = row.get("one_line_hint") or "(no hint)"
    title = " ".join(str(row.get("title") or "").split())
    return f"{row['id']} | {vy} | {title} | {row.get('pdf_path')} | [rel {rel if rel is not None else '-'}] {hint}"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("terms", nargs="*", help="all terms must match (case-insensitive substring)")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="index directory")
    parser.add_argument("--min-relevance", type=int, default=None)
    parser.add_argument("--topic", action="append", default=None, help="require this topic (repeatable)")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--json", action="store_true", help="print matching rows as JSON lines")
    args = parser.parse_args(argv)
    rows = load_index(Path(args.out))
    if not rows:
        print(f"no catalog under {args.out}", file=sys.stderr)
        return 2
    hits = search(rows, args.terms, args.min_relevance, args.topic)
    shown = hits[: args.limit] if args.limit is not None else hits
    for row in shown:
        if args.json:
            print(json.dumps({k: v for k, v in row.items() if k != "abstract"}, ensure_ascii=False))
        else:
            print(format_row(row))
    print(f"{len(hits)} match(es) of {len(rows)} papers", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
