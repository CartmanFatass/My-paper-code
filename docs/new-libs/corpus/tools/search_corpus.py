"""Small dependency-free search interface for the local MARL corpus."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(f"{key} {text(item)}" for key, item in value.items())
    if isinstance(value, (list, tuple, set)):
        return " ".join(text(item) for item in value)
    return str(value)


def norm(value: Any) -> str:
    return re.sub(r"\s+", " ", text(value).casefold()).strip()


def tokens(query: str) -> list[str]:
    return re.findall(r"[\w.+-]+", query.casefold(), flags=re.UNICODE)


def contains_filter(row: dict[str, Any], key: str, wanted: str | None) -> bool:
    if not wanted:
        return True
    return wanted.casefold() in norm(row.get(key))


def score(row: dict[str, Any], query: str, fields: Iterable[tuple[str, int]]) -> int:
    if not query.strip():
        return 1
    phrase = norm(query)
    query_tokens = tokens(query)
    result = 0
    for field, weight in fields:
        haystack = norm(row.get(field))
        if phrase and phrase in haystack:
            result += weight * 8
        result += weight * sum(haystack.count(token) for token in query_tokens)
    return result


def collect(args: argparse.Namespace) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    search_rows = read_jsonl(ROOT / "search_index.jsonl")
    chunk_paths = {row["chunk_id"]: row["path"] for row in search_rows}
    if args.kind in {"all", "papers"}:
        for row in read_jsonl(ROOT / "catalog.jsonl"):
            if not contains_filter(row, "paper_id", args.paper):
                continue
            if not contains_filter(row, "hmasd_axes", args.axis):
                continue
            if not contains_filter(row, "primary_topics", args.topic):
                continue
            if not contains_filter(row, "evidence_types", args.evidence):
                continue
            value = score(
                row,
                args.query,
                (
                    ("title", 8),
                    ("primary_topics", 6),
                    ("method_families", 6),
                    ("problem_classes", 4),
                    ("hmasd_axes", 4),
                    ("evidence_types", 3),
                ),
            )
            if value:
                results.append(
                    {
                        "result_kind": "paper",
                        "score": value,
                        "paper_id": row["paper_id"],
                        "title": row["title"],
                        "path": row["overview_path"],
                        "pdf_pages": [],
                        "summary": "; ".join(row.get("primary_topics", [])),
                    }
                )
    if args.kind in {"all", "claims"}:
        for row in read_jsonl(ROOT / "claim_index.jsonl"):
            if not contains_filter(row, "paper_id", args.paper):
                continue
            if not contains_filter(row, "hmasd_axes", args.axis):
                continue
            if not contains_filter(row, "topics", args.topic):
                continue
            if not contains_filter(row, "evidence_type", args.evidence):
                continue
            value = score(
                row,
                args.query,
                (
                    ("statement", 10),
                    ("conditions", 6),
                    ("limits", 6),
                    ("topics", 5),
                    ("hmasd_axes", 4),
                    ("evidence_type", 3),
                ),
            )
            if value:
                related = row.get("related_chunk_ids", [])
                related_paths = [chunk_paths[chunk] for chunk in related]
                chunk_path = related_paths[0] if related_paths else ""
                results.append(
                    {
                        "result_kind": row.get("claim_kind", "claim"),
                        "score": value,
                        "paper_id": row["paper_id"],
                        "title": row.get("claim_id", ""),
                        "path": chunk_path,
                        "pdf_pages": row.get("pdf_pages", []),
                        "summary": row.get("statement", ""),
                        "conditions": row.get("conditions", ""),
                        "limits": row.get("limits", ""),
                        "related_paths": related_paths,
                    }
                )
    if args.kind in {"all", "chunks"}:
        for row in search_rows:
            if not contains_filter(row, "paper_id", args.paper):
                continue
            if args.axis or args.evidence:
                # Axis/evidence filters are semantic claim/paper filters, not
                # guessed from page text.
                continue
            if not contains_filter(row, "keywords", args.topic):
                continue
            value = score(
                row,
                args.query,
                (
                    ("summary", 10),
                    ("keywords", 7),
                    ("section_path", 6),
                    ("content_types", 4),
                ),
            )
            if value:
                results.append(
                    {
                        "result_kind": "chunk",
                        "score": value,
                        "paper_id": row["paper_id"],
                        "title": row["chunk_id"],
                        "path": row["path"],
                        "pdf_pages": row.get("pdf_pages", []),
                        "summary": row.get("summary", ""),
                        "warnings": row.get("extraction_warnings", []),
                    }
                )
    return sorted(
        results,
        key=lambda row: (-int(row["score"]), row["paper_id"], row["title"]),
    )[: args.limit]


def render_markdown(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No matching corpus record."
    lines: list[str] = []
    for row in rows:
        pages = row.get("pdf_pages") or []
        locator = f"; PDF pages {pages}" if pages else ""
        lines.append(
            f"- **{row['paper_id']} / {row['result_kind']} / score {row['score']}**"
            f"{locator}: [{row['title']}]({row['path']})"
        )
        if row.get("summary"):
            lines.append(f"  - {row['summary']}")
        if row.get("limits"):
            lines.append(f"  - Limits: {row['limits']}")
        if row.get("warnings"):
            lines.append(f"  - Extraction warnings: {row['warnings']}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", default="")
    parser.add_argument(
        "--kind", choices=("all", "papers", "claims", "chunks"), default="all"
    )
    parser.add_argument("--paper", help="paper ID substring, e.g. P14")
    parser.add_argument("--axis", help="HMASD axis filter")
    parser.add_argument("--topic", help="topic/keyword filter")
    parser.add_argument("--evidence", help="evidence-type filter")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = collect(args)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(rows))


if __name__ == "__main__":
    main()
