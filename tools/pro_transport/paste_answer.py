#!/usr/bin/env python3
"""Paste a captured Pro answer into the empty ``### Answer`` subsection of a NOTES question.

Fixed procedure (owner authorisation 2026-09-30: the session pastes Pro captures itself, as a
script, without a per-instance request).  The script is deliberately narrow:

* the target is the ``### Answer`` subsection directly under ``## Pro question <date> <key>``;
* it refuses when that subsection is not empty (never overwrites a pasted or hand-written answer);
* the answer text is inserted verbatim, preceded by one provenance line (capture path, sha256,
  character count, kind and the wait record's state);
* it refuses an answer that contains a ``## `` / ``### `` heading line (that would split the NOTES
  structure) — such a capture is pasted after manual review;
* ``--check`` reports what would happen and changes nothing.

Usage:
  paste_answer.py --notes <NOTES.md> --key <question key> --operation <scratch dir> [--check]

The operation directory holds ``answer.txt`` and ``wait.json`` (from ``jev_send.py wait``).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path


def find_answer_slot(lines: list[str], key: str) -> tuple[int, int, int]:
    """Return (question line, ``### Answer`` line, first line after the empty answer body)."""
    heads = [i for i, l in enumerate(lines) if l.startswith("## Pro question ") and l.rstrip().endswith(" " + key)]
    if len(heads) != 1:
        raise SystemExit(f"refused: {len(heads)} question headings end with key {key!r} (need exactly 1)")
    q = heads[0]
    a = None
    for i in range(q + 1, len(lines)):
        if lines[i].startswith("## "):
            break
        if lines[i].startswith("### Answer"):
            a = i
            break
    if a is None:
        raise SystemExit(f"refused: no '### Answer' subsection under the question {key!r}")
    end = len(lines)
    for i in range(a + 1, len(lines)):
        if lines[i].startswith("## ") or lines[i].startswith("### "):
            end = i
            break
    body = [l for l in lines[a + 1:end] if l.strip()]
    if body:
        raise SystemExit(f"refused: the Answer subsection of {key!r} already holds {len(body)} non-empty lines")
    return q, a, end


def load_capture(operation: Path) -> tuple[str, dict]:
    answer_path = operation / "answer.txt"
    wait_path = operation / "wait.json"
    if not answer_path.is_file():
        raise SystemExit(f"refused: {answer_path} missing")
    text = answer_path.read_text(encoding="utf-8")
    wait = json.loads(wait_path.read_text(encoding="utf-8")) if wait_path.is_file() else {}
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    stripped = hashlib.sha256(text.strip().encode("utf-8")).hexdigest()   # jev_send hashes the stripped answer
    recorded = wait.get("answer_sha256")
    if recorded and recorded not in (digest, stripped):
        raise SystemExit(f"refused: answer.txt sha256 {digest[:12]}/{stripped[:12]} != wait.json {recorded[:12]}")
    bad = [i + 1 for i, l in enumerate(text.split("\n")) if l.startswith("## ") or l.startswith("### ")]
    if bad:
        raise SystemExit(f"refused: answer lines {bad} are '##'/'###' headings; paste after manual review")
    return text, {"sha256": digest, "chars": len(text), "state": wait.get("state"), "kind": wait.get("kind")}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--notes", required=True, type=Path)
    ap.add_argument("--key", required=True)
    ap.add_argument("--operation", required=True, type=Path)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    raw = args.notes.read_text(encoding="utf-8")
    lines = raw.split("\n")
    q, a, end = find_answer_slot(lines, args.key)
    text, prov = load_capture(args.operation)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = (f"_Pasted verbatim by the fixed procedure `tools/pro_transport/paste_answer.py` at {stamp} "
              f"from `{args.operation.as_posix()}/answer.txt` (sha256 {prov['sha256'][:16]}…, "
              f"{prov['chars']} chars, {prov['kind'] or 'capture'}, wait state {prov['state']})._")
    body = ["", header, ""] + text.rstrip("\n").split("\n") + [""]
    print(f"{args.notes}: question line {q + 1}, Answer line {a + 1}, inserting {len(body)} lines "
          f"({prov['chars']} chars) {'[check only]' if args.check else ''}")
    if args.check:
        return 0
    new_lines = lines[:a + 1] + body + lines[end:]
    args.notes.write_text("\n".join(new_lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
