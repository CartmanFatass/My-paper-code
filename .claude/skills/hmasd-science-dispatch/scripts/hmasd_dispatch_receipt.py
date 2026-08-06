#!/usr/bin/env python3
"""Pre-dispatch gate: refuse to send a question whose numbers are not derived.

WHY THIS EXISTS
---------------
`.claude/ORCHESTRATOR_WORKFLOW.md` Section 2 already said "self-check before
dispatch", and two mechanically-findable defects were shipped to External Pro
anyway.  Prose the orchestrator reads is prose the orchestrator can under-apply.
This script is the part that cannot be under-applied: it exits non-zero, and the
dispatch procedure requires its receipt.

WHAT IT CHECKS, AND WHAT IT DOES NOT
------------------------------------
It answers one question mechanically: **is every substantive number in the
outgoing document traceable to something that was actually computed?**  It does
NOT check that the document's prose is true, that the science is sound, or that
the right question is being asked.  Those are, respectively, the clean-context
document reviewer's job and External Pro's job.

"Substantive" is deliberately narrow, because a checker with false positives
gets disabled:

    integers  >= 3 digits     300, 178317, 20260806  (budgets, sizes, seeds)
    floats    >= 2 decimals   4.4675, 0.5252223610877991
    hex       >= 8 chars      commit ids, sha256 digests, float32 byte patterns

Ordered-list markers, one-decimal section numbers and ISO dates fall below that
floor or are skipped explicitly.  A number that is genuinely prose (a count of
rounds, a year) goes in the manifest whitelist WITH A REASON, which is itself a
useful record: the whitelist is the list of numbers nobody recomputed.

THE MATCHING RULE
-----------------
A document literal matches a truth value when the document is a correct
rendering of it at the document's own precision -- `4.4675` matches
`4.467461307208166` because `round(4.467461307208166, 4) == 4.4675`.  Digests
match by prefix, because `1f08308e...` is how a digest is quoted.  Integers must
match exactly; prefix matching there would let `300` be satisfied by `30012345`.

DERIVED NUMBERS ARE NOT EXEMPT
------------------------------
A t-interval endpoint like `4.2807` appears in no artifact -- it is
`mean - half_width`.  Declaring a `command` truth source that prints it is the
point, not a workaround: if a derived number is in the document, something must
have derived it, and that something is now recorded and re-runnable.

USAGE
-----
    python hmasd_dispatch_receipt.py --item local_research/pro_reviews/<item>

reading `10_DISPATCH_MANIFEST.json` from that directory and writing
`30_DISPATCH_RECEIPT.json` beside it.  Exit 0 means dispatch is permitted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
from typing import Any, Iterable

SCHEMA_VERSION = 1
MANIFEST_NAME = "10_DISPATCH_MANIFEST.json"
RECEIPT_NAME = "30_DISPATCH_RECEIPT.json"
DEFAULT_QUESTION = "20_RAW_QUESTION.md"
DEFAULT_DOCUMENT_REVIEW = "15_DOCUMENT_REVIEW.md"
#: The clean-context reviewer's accepting terminal.  Anything else blocks.
DOCUMENT_REVIEW_ACCEPTS = "DOCUMENT_MATCHES_SOURCE"

MIN_INTEGER_DIGITS = 3
MIN_FLOAT_DECIMALS = 2
MIN_HEX_CHARS = 8

#: Removed from the document before literals are extracted.  Each entry is a
#: place where a number is structure rather than a claim.
DEFAULT_SKIP_PATTERNS = (
    r"20\d{2}-\d{2}-\d{2}",           # ISO dates
    r"https?://\S+",                   # URLs (commit ids inside them are cited elsewhere)
    r"(?m)^#{1,6}\s+[\d.]+",           # markdown heading numbers
    r"(?m)^\s{0,3}\d{1,2}\.\s",        # ordered list markers
    r"(?m)^\s{0,3}\|?\s*-{2,}",        # table rules
)

#: The trailing guards reject a version-like `1.2.3` and the integer part of a
#: float, but MUST still accept a number that ends a sentence.  The first draft
#: used `(?![\w.])`, which silently skipped every figure written as `4.4675.` --
#: i.e. most figures in prose.  A gate with a hole that size is worse than no
#: gate, because it reports a pass.  `test_a_number_that_was_never_computed_
#: blocks_dispatch` is what caught it.
_FLOAT_RE = re.compile(r"(?<![\w.])(\d+)\.(\d+)(?!\d)(?!\.\d)")
_INT_RE = re.compile(r"(?<![\w.])(\d+)(?!\.\d)(?![\w])")
_HEX_RE = re.compile(r"(?<![\w])([0-9a-f]{%d,64})(?![\w])" % MIN_HEX_CHARS)


class GateError(RuntimeError):
    """The manifest itself is unusable; nothing was checked."""


# ---------------------------------------------------------------------------
# Literal extraction
# ---------------------------------------------------------------------------


def strip_skipped(text: str, patterns: Iterable[str]) -> str:
    for pattern in patterns:
        text = re.sub(pattern, " ", text)
    return text


def document_literals(text: str, *, skip_patterns: Iterable[str]) -> dict[str, set[str]]:
    """The substantive literals a reader would treat as claims."""
    stripped = strip_skipped(text, skip_patterns)
    floats = {
        f"{whole}.{decimals}"
        for whole, decimals in _FLOAT_RE.findall(stripped)
        if len(decimals) >= MIN_FLOAT_DECIMALS
    }
    integers = {
        value
        for value in _INT_RE.findall(stripped)
        if len(value.lstrip("0") or "0") >= MIN_INTEGER_DIGITS
    }
    hexes = {value for value in _HEX_RE.findall(stripped) if not value.isdigit()}
    return {"floats": floats, "integers": integers, "hex": hexes}


def truth_literals(text: str) -> dict[str, set[str]]:
    """Every number a truth source contains, at full precision.

    No minimum size here: a truth source is allowed to be the authority for a
    two-digit number that the document happens to quote.
    """
    floats = {f"{whole}.{decimals}" for whole, decimals in _FLOAT_RE.findall(text)}
    integers = set(_INT_RE.findall(text))
    hexes = {value for value in _HEX_RE.findall(text) if not value.isdigit()}
    return {"floats": floats, "integers": integers, "hex": hexes}


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------


def float_matches(literal: str, truths: set[str]) -> bool:
    """`4.4675` matches `4.467461307208166`: correct at the document's precision."""
    if literal in truths:
        return True
    decimals = len(literal.split(".", 1)[1])
    try:
        target = float(literal)
    except ValueError:
        return False
    for candidate in truths:
        if candidate.startswith(literal):
            return True
        try:
            value = float(candidate)
        except ValueError:
            continue
        if round(value, decimals) == target:
            return True
    return False


def hex_matches(literal: str, truths: set[str]) -> bool:
    """Digests are quoted by prefix, so a prefix is an honest citation."""
    return any(candidate.startswith(literal) for candidate in truths)


def integer_matches(literal: str, truths: dict[str, set[str]]) -> bool:
    """Exact only. Prefix matching would let 300 be satisfied by 30012345.

    A float truth also authorizes its own integer part written without a
    decimal point, which is how counts read back out of JSON.
    """
    if literal in truths["integers"]:
        return True
    return any(candidate.split(".", 1)[0] == literal for candidate in truths["floats"])


# ---------------------------------------------------------------------------
# Truth sources and preconditions
# ---------------------------------------------------------------------------


def _run(argv: list[str], *, cwd: pathlib.Path, timeout: int = 1800) -> dict[str, Any]:
    completed = subprocess.run(
        argv, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )
    return {
        "argv": list(argv),
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr[-4000:],
    }


def collect_truth(
    sources: list[dict[str, Any]], *, root: pathlib.Path
) -> tuple[dict[str, set[str]], list[dict[str, Any]]]:
    combined = {"floats": set(), "integers": set(), "hex": set()}
    records: list[dict[str, Any]] = []
    for source in sources:
        kind = source.get("kind")
        if kind in ("json", "text"):
            path = root / source["path"]
            if not path.is_file():
                raise GateError(f"truth source missing: {source['path']}")
            raw = path.read_bytes()
            text = raw.decode("utf-8", errors="replace")
            records.append(
                {
                    "kind": kind,
                    "path": source["path"],
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            )
        elif kind == "command":
            result = _run(
                list(source["argv"]), cwd=root / source.get("cwd", "."),
            )
            if result["exit_code"] != 0:
                raise GateError(
                    f"truth command failed: {source['argv']} -> {result['stderr']}"
                )
            text = result["stdout"]
            records.append(
                {
                    "kind": kind,
                    "argv": result["argv"],
                    "stdout_bytes": len(text),
                    "stdout_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                }
            )
        else:
            raise GateError(f"unknown truth source kind {kind!r}")
        found = truth_literals(text)
        for key in combined:
            combined[key] |= found[key]
    return combined, records


def check_numbers(
    question: str, truth: dict[str, set[str]], whitelist: dict[str, str],
    *, skip_patterns: Iterable[str],
) -> dict[str, Any]:
    literals = document_literals(question, skip_patterns=skip_patterns)
    untraceable: list[dict[str, str]] = []
    for value in sorted(literals["floats"]):
        if value in whitelist or float_matches(value, truth["floats"]):
            continue
        untraceable.append({"literal": value, "kind": "float"})
    for value in sorted(literals["integers"]):
        if value in whitelist or integer_matches(value, truth):
            continue
        untraceable.append({"literal": value, "kind": "integer"})
    for value in sorted(literals["hex"]):
        if value in whitelist or hex_matches(value, truth["hex"]):
            continue
        untraceable.append({"literal": value, "kind": "hex"})
    return {
        "checked": {key: len(values) for key, values in literals.items()},
        "whitelisted": sorted(whitelist),
        "untraceable": untraceable,
        "passed": not untraceable,
    }


def check_preconditions(
    preconditions: list[dict[str, Any]], *, root: pathlib.Path
) -> dict[str, Any]:
    rows = []
    for entry in preconditions:
        result = _run(list(entry["argv"]), cwd=root / entry.get("cwd", "."))
        expected = int(entry.get("expect_exit", 0))
        expect_empty = bool(entry.get("expect_empty_stdout", False))
        passed = result["exit_code"] == expected and (
            not expect_empty or not result["stdout"].strip()
        )
        rows.append(
            {
                "name": entry["name"],
                "argv": result["argv"],
                "exit_code": result["exit_code"],
                "expected_exit": expected,
                "expect_empty_stdout": expect_empty,
                "stdout_tail": result["stdout"][-800:],
                "passed": passed,
            }
        )
    return {"checks": rows, "passed": all(row["passed"] for row in rows)}


def check_document_review(
    path: pathlib.Path | None, *, required: bool
) -> dict[str, Any]:
    """The clean-context reviewer's verdict on the outgoing document.

    Required by default and separate from the number check, because they catch
    different things: the number check proves each figure was computed, the
    reviewer proves the prose describes the code that computed it.  Every
    registration round that was rejected for a prose/code mismatch would have
    been visible to a reader holding both.
    """
    if not required:
        return {"required": False, "passed": True}
    if path is None or not path.is_file():
        return {
            "required": True,
            "passed": False,
            "detail": f"missing {DEFAULT_DOCUMENT_REVIEW}: a clean-context "
            "document review is mandatory before dispatch",
        }
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    terminal = text.splitlines()[-1].strip() if text else ""
    return {
        "required": True,
        "path": str(path.name),
        "terminal": terminal,
        "passed": terminal == DOCUMENT_REVIEW_ACCEPTS,
        "detail": f"final line must be exactly {DOCUMENT_REVIEW_ACCEPTS}",
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def build_receipt(item: pathlib.Path, *, root: pathlib.Path) -> dict[str, Any]:
    manifest_path = item / MANIFEST_NAME
    if not manifest_path.is_file():
        raise GateError(f"no {MANIFEST_NAME} in {item}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    question_path = item / manifest.get("question", DEFAULT_QUESTION)
    if not question_path.is_file():
        raise GateError(f"question not found: {question_path}")
    question_bytes = question_path.read_bytes()
    question = question_bytes.decode("utf-8", errors="replace")

    skip_patterns = tuple(DEFAULT_SKIP_PATTERNS) + tuple(
        manifest.get("extra_skip_patterns", ())
    )
    truth, truth_records = collect_truth(
        list(manifest.get("truth_sources", ())), root=root
    )
    numbers = check_numbers(
        question,
        truth,
        dict(manifest.get("whitelist", {})),
        skip_patterns=skip_patterns,
    )
    preconditions = check_preconditions(
        list(manifest.get("preconditions", ())), root=root
    )
    review_name = manifest.get("document_review", DEFAULT_DOCUMENT_REVIEW)
    review = check_document_review(
        item / review_name if review_name else None,
        required=bool(manifest.get("document_review_required", True)),
    )

    passed = numbers["passed"] and preconditions["passed"] and review["passed"]
    return {
        "schema_version": SCHEMA_VERSION,
        "item": item.name,
        "question": {
            "path": question_path.name,
            "bytes": len(question_bytes),
            "sha256": hashlib.sha256(question_bytes).hexdigest(),
        },
        "truth_sources": truth_records,
        "truth_literal_counts": {key: len(values) for key, values in truth.items()},
        "number_traceability": numbers,
        "preconditions": preconditions,
        "document_review": review,
        "terminal": "DISPATCH_PERMITTED" if passed else "DISPATCH_BLOCKED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--item", required=True, help="review item directory")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="repository root; defaults to four parents above this script",
    )
    arguments = parser.parse_args()

    root = (
        pathlib.Path(arguments.repo_root).resolve()
        if arguments.repo_root
        else pathlib.Path(__file__).resolve().parents[4]
    )
    item = (root / arguments.item).resolve()

    try:
        receipt = build_receipt(item, root=root)
    except GateError as error:
        print(f"DISPATCH_BLOCKED: {error}", file=sys.stderr)
        return 2

    (item / RECEIPT_NAME).write_bytes(
        json.dumps(receipt, indent=2, sort_keys=True).encode("utf-8")
    )
    print(f"terminal: {receipt['terminal']}")
    print(f"receipt:  {item / RECEIPT_NAME}")
    if receipt["terminal"] != "DISPATCH_PERMITTED":
        for row in receipt["number_traceability"]["untraceable"]:
            print(f"  untraceable {row['kind']}: {row['literal']}", file=sys.stderr)
        for row in receipt["preconditions"]["checks"]:
            if not row["passed"]:
                print(f"  precondition failed: {row['name']}", file=sys.stderr)
        if not receipt["document_review"]["passed"]:
            print(
                f"  document review: {receipt['document_review'].get('detail')}",
                file=sys.stderr,
            )
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
