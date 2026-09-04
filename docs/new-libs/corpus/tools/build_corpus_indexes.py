"""Merge and validate the local new-libs LLM corpus.

This script is intentionally deterministic. It reads per-paper artifacts and
writes the machine-readable global catalog/search/claim indexes plus QA reports.
It never reads or rewrites PDF content.
"""

from __future__ import annotations

import json
import hashlib
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
PAPERS = ROOT / "papers"
QA = ROOT / "qa"

EXPECTED_IDS = (
    "B01",
    "B02",
    "B03",
    "P01",
    "P02",
    "P03",
    "P04",
    "P05",
    "P06",
    "P07",
    "P08",
    "P09",
    "P10",
    "P11",
    "P12",
    "P13",
    "P14",
    "P15",
    "P16",
    "P17",
    "P18",
    "P19",
    "P20",
    "P21",
    "P22",
    "P24",
    "P25",
)

OVERVIEW_HEADINGS = (
    "Identity and scope",
    "Problem formulation",
    "Actual contribution",
    "Core objects and equations",
    "Algorithms or mechanism primitives",
    "Assumptions and information structure",
    "Theorems and guarantees",
    "Experiments and evaluation protocol",
    "Failure boundaries and non-claims",
    "HMASD prospective connections",
    "Recommended reading route",
    "Source-page anchors",
)

ALLOWED_CLAIM_KINDS = {
    "source_claim",
    "source_scope",
    "curator_boundary",
    "curator_connection",
}


class CorpusError(RuntimeError):
    pass


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - diagnostic wrapper
        raise CorpusError(f"Invalid JSON: {path}: {exc}") from exc


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception as exc:  # pragma: no cover - diagnostic wrapper
            raise CorpusError(f"Invalid JSONL: {path}:{number}: {exc}") from exc
        if not isinstance(row, dict):
            raise CorpusError(f"JSONL row is not an object: {path}:{number}")
        rows.append(row)
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
        ),
        encoding="utf-8",
    )


def require_keys(row: dict[str, Any], keys: Iterable[str], context: str) -> None:
    missing = [key for key in keys if key not in row]
    if missing:
        raise CorpusError(f"{context} missing keys: {', '.join(missing)}")


def forbidden_controls(value: str) -> list[int]:
    return [
        ord(character)
        for character in value
        if ord(character) < 32 and character not in "\n\r\t"
    ]


def repo_path(raw: str, context: str) -> Path:
    path = (REPO / raw).resolve()
    try:
        path.relative_to(REPO.resolve())
    except ValueError as exc:
        raise CorpusError(f"{context} escapes repository: {raw}") from exc
    return path


def paper_sort_key(paper_id: str) -> tuple[str, int]:
    match = re.fullmatch(r"([A-Z]+)(\d+)", paper_id)
    if not match:
        return paper_id, 0
    return match.group(1), int(match.group(2))


def main() -> None:
    errors: list[str] = []
    warnings: list[dict[str, Any]] = []
    catalog: list[dict[str, Any]] = []
    chunks: list[dict[str, Any]] = []
    claims: list[dict[str, Any]] = []
    global_chunk_ids: set[str] = set()
    global_claim_ids: set[str] = set()
    topic_map: dict[str, list[str]] = defaultdict(list)
    method_map: dict[str, list[str]] = defaultdict(list)
    axis_map: dict[str, list[str]] = defaultdict(list)
    evidence_map: dict[str, list[str]] = defaultdict(list)

    actual_ids = sorted(
        (path.name for path in PAPERS.iterdir() if path.is_dir()),
        key=paper_sort_key,
    ) if PAPERS.exists() else []
    if set(actual_ids) != set(EXPECTED_IDS):
        missing = sorted(set(EXPECTED_IDS) - set(actual_ids), key=paper_sort_key)
        extra = sorted(set(actual_ids) - set(EXPECTED_IDS), key=paper_sort_key)
        errors.append(f"paper directories mismatch; missing={missing}; extra={extra}")

    for paper_id in EXPECTED_IDS:
        base = PAPERS / paper_id
        required = (
            base / "metadata.json",
            base / "overview.md",
            base / "structure.json",
            base / "claims.jsonl",
            base / "chunks.jsonl",
        )
        missing_files = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
        if missing_files:
            errors.append(f"{paper_id}: missing files {missing_files}")
            continue

        try:
            metadata = read_json(base / "metadata.json")
            if not isinstance(metadata, dict):
                raise CorpusError(f"{paper_id}: metadata is not an object")
            require_keys(
                metadata,
                (
                    "paper_id",
                    "title",
                    "authors",
                    "year",
                    "source_pdf",
                    "pdf_pages",
                    "primary_topics",
                    "method_families",
                    "evidence_types",
                    "hmasd_axes",
                    "content_fingerprint",
                ),
                f"{paper_id} metadata",
            )
            if metadata["paper_id"] != paper_id:
                raise CorpusError(
                    f"{paper_id}: metadata paper_id={metadata['paper_id']!r}"
                )
            source_pdf = repo_path(str(metadata["source_pdf"]), f"{paper_id} source_pdf")
            if not source_pdf.is_file():
                raise CorpusError(f"{paper_id}: missing source PDF {source_pdf}")
            actual_pages = len(PdfReader(str(source_pdf)).pages)
            if int(metadata["pdf_pages"]) != actual_pages:
                raise CorpusError(
                    f"{paper_id}: metadata pdf_pages={metadata['pdf_pages']} "
                    f"but source has {actual_pages}"
                )
            fingerprint = str(metadata["content_fingerprint"])
            expected_fingerprint = "sha256:" + hashlib.sha256(
                source_pdf.read_bytes()
            ).hexdigest()
            if fingerprint != expected_fingerprint:
                raise CorpusError(
                    f"{paper_id}: content_fingerprint does not match source PDF"
                )
            for warning_page in metadata.get("warning_pages", []):
                if int(warning_page) < 1 or int(warning_page) > actual_pages:
                    raise CorpusError(
                        f"{paper_id}: warning page {warning_page} out of range"
                    )

            overview = (base / "overview.md").read_text(encoding="utf-8")
            overview_controls = forbidden_controls(overview)
            if overview_controls:
                errors.append(
                    f"{paper_id}: overview contains forbidden controls "
                    f"{sorted(set(overview_controls))}"
                )
            for heading in OVERVIEW_HEADINGS:
                if not re.search(rf"^#+\s+{re.escape(heading)}\s*$", overview, re.MULTILINE):
                    errors.append(f"{paper_id}: overview missing heading {heading!r}")

            structure = read_json(base / "structure.json")
            if not isinstance(structure, (dict, list)):
                errors.append(f"{paper_id}: structure.json must be object or array")

            paper_chunks = read_jsonl(base / "chunks.jsonl")
            if "chunk_count" in metadata and int(metadata["chunk_count"]) != len(
                paper_chunks
            ):
                raise CorpusError(
                    f"{paper_id}: metadata chunk_count does not match chunks.jsonl"
                )
            seen_pages: set[int] = set()
            last_page = 0
            for ordinal, row in enumerate(paper_chunks, 1):
                require_keys(
                    row,
                    (
                        "chunk_id",
                        "paper_id",
                        "path",
                        "pdf_pages",
                        "section_path",
                        "content_types",
                        "keywords",
                        "summary",
                        "word_count",
                        "extraction_warnings",
                    ),
                    f"{paper_id} chunk {ordinal}",
                )
                chunk_id = str(row["chunk_id"])
                if chunk_id in global_chunk_ids:
                    raise CorpusError(f"duplicate chunk_id {chunk_id}")
                global_chunk_ids.add(chunk_id)
                if row["paper_id"] != paper_id:
                    raise CorpusError(f"{chunk_id}: wrong paper_id {row['paper_id']!r}")
                pages = [int(page) for page in row["pdf_pages"]]
                if not pages or pages != list(range(pages[0], pages[-1] + 1)):
                    raise CorpusError(f"{chunk_id}: pages must be contiguous")
                if len(pages) > 6:
                    raise CorpusError(f"{chunk_id}: more than six PDF pages")
                if pages[0] <= last_page:
                    raise CorpusError(f"{chunk_id}: overlapping/nonmonotone page span")
                if pages[0] < 1 or pages[-1] > actual_pages:
                    raise CorpusError(f"{chunk_id}: page out of range")
                last_page = pages[-1]
                seen_pages.update(pages)
                chunk_path = repo_path(str(row["path"]), f"{chunk_id} path")
                if not chunk_path.is_file():
                    raise CorpusError(f"{chunk_id}: missing chunk file {chunk_path}")
                text = chunk_path.read_text(encoding="utf-8")
                chunk_controls = forbidden_controls(text)
                if chunk_controls:
                    errors.append(
                        f"{chunk_id}: contains forbidden controls "
                        f"{sorted(set(chunk_controls))}"
                    )
                if "[CONTROL U+" in text and "scan_or_font_issue" not in row.get(
                    "extraction_warnings", []
                ):
                    errors.append(
                        f"{chunk_id}: explicit control marker lacks scan_or_font_issue"
                    )
                for page in pages:
                    if f"[PDF page {page}]" not in text:
                        errors.append(f"{chunk_id}: missing marker [PDF page {page}]")
                normalized = dict(row)
                normalized["ordinal"] = ordinal
                chunks.append(normalized)
                for warning in row.get("extraction_warnings", []):
                    warnings.append(
                        {
                            "paper_id": paper_id,
                            "chunk_id": chunk_id,
                            "pdf_pages": pages,
                            "warning": warning,
                        }
                    )
            expected_pages = set(range(1, actual_pages + 1))
            if seen_pages != expected_pages:
                errors.append(
                    f"{paper_id}: chunk page coverage missing="
                    f"{sorted(expected_pages - seen_pages)} extra={sorted(seen_pages - expected_pages)}"
                )

            paper_claims = read_jsonl(base / "claims.jsonl")
            paper_chunk_pages = {
                row["chunk_id"]: set(int(page) for page in row["pdf_pages"])
                for row in paper_chunks
            }
            for ordinal, row in enumerate(paper_claims, 1):
                require_keys(
                    row,
                    (
                        "claim_id",
                        "paper_id",
                        "claim_kind",
                        "statement",
                        "pdf_pages",
                        "evidence_type",
                        "conditions",
                        "limits",
                        "topics",
                        "hmasd_axes",
                        "related_chunk_ids",
                    ),
                    f"{paper_id} claim {ordinal}",
                )
                claim_id = str(row["claim_id"])
                if claim_id in global_claim_ids:
                    raise CorpusError(f"duplicate claim_id {claim_id}")
                global_claim_ids.add(claim_id)
                if row["paper_id"] != paper_id:
                    raise CorpusError(f"{claim_id}: wrong paper_id")
                if row["claim_kind"] not in ALLOWED_CLAIM_KINDS:
                    raise CorpusError(
                        f"{claim_id}: invalid claim_kind {row['claim_kind']!r}"
                    )
                claim_pages = [int(page) for page in row["pdf_pages"]]
                if any(page < 1 or page > actual_pages for page in claim_pages):
                    raise CorpusError(f"{claim_id}: page out of range")
                missing_chunks = sorted(
                    set(row["related_chunk_ids"]) - global_chunk_ids
                )
                if missing_chunks:
                    raise CorpusError(
                        f"{claim_id}: unknown related chunks {missing_chunks}"
                    )
                covered_claim_pages: set[int] = set()
                for chunk_id in row["related_chunk_ids"]:
                    covered_claim_pages.update(paper_chunk_pages[chunk_id])
                missing_claim_pages = sorted(set(claim_pages) - covered_claim_pages)
                if missing_claim_pages:
                    raise CorpusError(
                        f"{claim_id}: related chunks do not cover pages "
                        f"{missing_claim_pages}"
                    )
                claims.append(dict(row))

            metadata = dict(metadata)
            metadata["chunk_count"] = len(paper_chunks)
            metadata["claim_count"] = len(paper_claims)
            metadata["overview_path"] = str(
                (base / "overview.md").relative_to(REPO).as_posix()
            )
            catalog.append(metadata)
            for topic in metadata.get("primary_topics", []):
                topic_map[str(topic)].append(paper_id)
            for method in metadata.get("method_families", []):
                method_map[str(method)].append(paper_id)
            for axis in metadata.get("hmasd_axes", []):
                axis_map[str(axis)].append(paper_id)
            for evidence in metadata.get("evidence_types", []):
                evidence_map[str(evidence)].append(paper_id)
        except CorpusError as exc:
            errors.append(str(exc))

    if errors:
        raise CorpusError("Corpus validation failed:\n- " + "\n- ".join(errors))

    write_json(ROOT / "catalog.json", catalog)
    write_jsonl(ROOT / "catalog.jsonl", catalog)
    write_jsonl(ROOT / "search_index.jsonl", chunks)
    write_jsonl(ROOT / "claim_index.jsonl", claims)
    write_json(
        ROOT / "navigation_facets.json",
        {
            "by_topic": {key: value for key, value in sorted(topic_map.items())},
            "by_method": {key: value for key, value in sorted(method_map.items())},
            "by_hmasd_axis": {key: value for key, value in sorted(axis_map.items())},
            "by_evidence_type": {
                key: value for key, value in sorted(evidence_map.items())
            },
        },
    )

    QA.mkdir(parents=True, exist_ok=True)
    total_pages = sum(int(row["pdf_pages"]) for row in catalog)
    total_words = sum(int(row["word_count"]) for row in chunks)
    coverage_lines = [
        "# Corpus coverage",
        "",
        "Generated by `tools/build_corpus_indexes.py` after strict validation.",
        "",
        f"- Papers: {len(catalog)}/{len(EXPECTED_IDS)}",
        f"- Source PDF pages represented: {total_pages}",
        f"- Page-aligned chunks: {len(chunks)}",
        f"- Approximate extracted words: {total_words}",
        f"- Indexed claims/boundaries/connections: {len(claims)}",
        f"- Chunk-level extraction warnings: {len(warnings)}",
        "",
        "| ID | Pages | Chunks | Claims | Overview |",
        "|---|---:|---:|---:|---|",
    ]
    for row in catalog:
        coverage_lines.append(
            f"| {row['paper_id']} | {row['pdf_pages']} | {row['chunk_count']} | "
            f"{row['claim_count']} | [{row['title']}]"
            f"(../papers/{row['paper_id']}/overview.md) |"
        )
    (QA / "COVERAGE.md").write_text("\n".join(coverage_lines) + "\n", encoding="utf-8")

    warning_lines = [
        "# Extraction warnings",
        "",
        "Warnings are routing signals, not silently repaired source content.",
        "",
    ]
    if not warnings:
        warning_lines.append("No chunk-level extraction warning was declared.")
    else:
        warning_lines.extend(
            f"- `{row['chunk_id']}` PDF pages {row['pdf_pages']}: {row['warning']}"
            for row in warnings
        )
    (QA / "EXTRACTION_WARNINGS.md").write_text(
        "\n".join(warning_lines) + "\n", encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "papers": len(catalog),
                "pages": total_pages,
                "chunks": len(chunks),
                "words": total_words,
                "claims": len(claims),
                "warnings": len(warnings),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
