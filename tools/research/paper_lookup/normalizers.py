"""Dependency-free normalizers for recorded scholarly API responses.

Adapted from K-Dense Inc.'s MIT-licensed paper-lookup scripts:
- skills/paper-lookup/scripts/arxiv_atom.py
- skills/paper-lookup/scripts/openalex_abstract.py
- skills/paper-lookup/scripts/jats_to_text.py
- skills/paper-lookup/scripts/_common.py
at commit f6fcafeb1cc8c82eca0160a18bc41c38427b8e0f.

Copyright (c) 2025 K-Dense Inc.
MIT License: permission is hereby granted, free of charge, to use, copy,
modify, merge, publish, distribute, sublicense, and/or sell copies, subject
to inclusion of this copyright and permission notice in copies or substantial
portions. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

This local adaptation deliberately accepts recorded data only. It does not
perform network I/O or infer absent source metadata.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections.abc import Mapping, Sequence
from typing import Any

ARXIV_NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
}

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_WHITESPACE = re.compile(r"\s+")
_SKIP_JATS_TAGS = frozenset({"xref", "label", "table-wrap", "graphic", "media", "inline-formula"})
_BLOCK_JATS_TAGS = frozenset({"abstract", "body", "caption", "def-item", "disp-quote", "list-item", "p", "sec", "statement", "td", "th", "title", "tr"})


class PaperLookupInputError(ValueError):
    """A local fixture is malformed or represents a documented false success."""


def collapse_whitespace(value: str | None) -> str:
    if not value:
        return ""
    return _WHITESPACE.sub(" ", _CONTROL.sub("", value)).strip()


def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PaperLookupInputError(f"{name} must be an object, not {type(value).__name__}")
    return value


def _arxiv_identifier(url: str) -> tuple[str, str | None, str | None]:
    versioned = url.rstrip("/").rsplit("/", 1)[-1]
    base, separator, version = versioned.rpartition("v")
    if separator and base and version.isdigit():
        return base, versioned, version
    return versioned, versioned or None, None


def _arxiv_link(entry: ET.Element, rel: str, mime: str) -> str | None:
    for link in entry.findall("atom:link", ARXIV_NAMESPACES):
        if link.get("rel") == rel and link.get("type") == mime:
            return link.get("href")
    return None


def normalize_arxiv_atom(xml_text: str) -> dict[str, Any]:
    """Normalize a recorded arXiv Atom response and reject HTTP-200 error feeds."""
    if xml_text.strip().startswith("Rate exceeded"):
        raise PaperLookupInputError("arXiv throttle payload: Rate exceeded")
    try:
        feed = ET.fromstring(xml_text)
    except ET.ParseError as error:
        raise PaperLookupInputError(f"arXiv payload is not XML: {error}") from error

    entries = feed.findall("atom:entry", ARXIV_NAMESPACES)
    for entry in entries:
        if collapse_whitespace(entry.findtext("atom:title", namespaces=ARXIV_NAMESPACES)) == "Error":
            reason = collapse_whitespace(entry.findtext("atom:summary", namespaces=ARXIV_NAMESPACES))
            raise PaperLookupInputError(f"arXiv HTTP-200 error feed: {reason or 'no reason given'}")

    records: list[dict[str, Any]] = []
    for entry in entries:
        raw_id = collapse_whitespace(entry.findtext("atom:id", namespaces=ARXIV_NAMESPACES))
        arxiv_id, versioned_id, version = _arxiv_identifier(raw_id) if raw_id else ("", None, None)
        categories = [
            term
            for term in (item.get("term") for item in entry.findall("atom:category", ARXIV_NAMESPACES))
            if term
        ]
        primary = entry.find("arxiv:primary_category", ARXIV_NAMESPACES)
        records.append(
            {
                "abstract": collapse_whitespace(entry.findtext("atom:summary", namespaces=ARXIV_NAMESPACES)) or None,
                "abstract_url": _arxiv_link(entry, "alternate", "text/html"),
                "arxiv_id": arxiv_id or None,
                "arxiv_id_versioned": versioned_id,
                "authors": [
                    name
                    for name in (
                        collapse_whitespace(author.findtext("atom:name", namespaces=ARXIV_NAMESPACES))
                        for author in entry.findall("atom:author", ARXIV_NAMESPACES)
                    )
                    if name
                ],
                "categories": categories,
                "doi": collapse_whitespace(entry.findtext("arxiv:doi", namespaces=ARXIV_NAMESPACES)) or None,
                "pdf_url": _arxiv_link(entry, "related", "application/pdf"),
                "primary_category": primary.get("term") if primary is not None else None,
                "published": collapse_whitespace(entry.findtext("atom:published", namespaces=ARXIV_NAMESPACES)) or None,
                "title": collapse_whitespace(entry.findtext("atom:title", namespaces=ARXIV_NAMESPACES)) or None,
                "updated": collapse_whitespace(entry.findtext("atom:updated", namespaces=ARXIV_NAMESPACES)) or None,
                "version": version,
            }
        )

    total = collapse_whitespace(feed.findtext("opensearch:totalResults", namespaces=ARXIV_NAMESPACES))
    return {
        "entries": records,
        "query_as_executed": collapse_whitespace(feed.findtext("atom:title", namespaces=ARXIV_NAMESPACES)) or None,
        "returned": len(records),
        "total_results": int(total) if total.isdigit() else None,
    }


def reconstruct_openalex_abstract(inverted_index: Mapping[str, Any]) -> tuple[str, list[str]]:
    """Reconstruct an OpenAlex inverted abstract without dropping collisions."""
    buckets: dict[int, list[str]] = {}
    warnings: list[str] = []
    for token, positions in inverted_index.items():
        if not isinstance(token, str):
            warnings.append(f"non-string token {token!r} ignored")
            continue
        if not isinstance(positions, list):
            warnings.append(f"positions for {token!r} are not a list")
            continue
        for position in positions:
            if not isinstance(position, int) or isinstance(position, bool) or position < 0:
                warnings.append(f"invalid position {position!r} for {token!r}")
                continue
            buckets.setdefault(position, []).append(token)

    if not buckets:
        return "", warnings
    ordered_positions = sorted(buckets)
    collisions = sum(len(tokens) > 1 for tokens in buckets.values())
    if collisions:
        warnings.append(f"{collisions} position(s) have multiple tokens; retained index order")
    missing = ordered_positions[-1] - ordered_positions[0] + 1 - len(ordered_positions)
    if missing:
        warnings.append(f"{missing} position(s) are absent from the inverted index")
    if ordered_positions[0] != 0:
        warnings.append(f"inverted index starts at {ordered_positions[0]}, not 0")
    return collapse_whitespace(" ".join(" ".join(buckets[position]) for position in ordered_positions)), warnings


def normalize_openalex(payload: Any) -> dict[str, Any]:
    """Normalize one work, a work list, or an OpenAlex ``results`` response."""
    if isinstance(payload, Mapping) and payload.get("error"):
        raise PaperLookupInputError(f"OpenAlex HTTP-200 error payload: {payload['error']}")
    if isinstance(payload, Mapping):
        works: Sequence[Any] = payload["results"] if isinstance(payload.get("results"), list) else [payload]
    elif isinstance(payload, list):
        works = payload
    else:
        raise PaperLookupInputError(f"OpenAlex payload must be an object or list, not {type(payload).__name__}")

    normalized: list[dict[str, Any]] = []
    for position, candidate in enumerate(works):
        work = _require_mapping(candidate, f"OpenAlex work at index {position}")
        index = work.get("abstract_inverted_index")
        record: dict[str, Any] = {
            "abstract": None,
            "doi": work.get("doi") if isinstance(work.get("doi"), str) else None,
            "id": work.get("id") if isinstance(work.get("id"), str) else None,
            "publication_year": work.get("publication_year") if isinstance(work.get("publication_year"), int) else None,
            "title": collapse_whitespace(work.get("title") or work.get("display_name")) or None,
        }
        if isinstance(index, Mapping) and index:
            abstract, warnings = reconstruct_openalex_abstract(index)
            record["abstract"] = abstract or None
            record["abstract_word_count"] = len(abstract.split()) if abstract else 0
            if warnings:
                record["abstract_warnings"] = warnings
        else:
            record["abstract_warnings"] = [
                "no abstract_inverted_index: OpenAlex may lack it or it may have been excluded by select"
            ]
        normalized.append(record)
    return {
        "count": len(normalized),
        "with_abstract": sum(record["abstract"] is not None for record in normalized),
        "works": normalized,
    }


def _jats_text(element: ET.Element) -> str:
    parts: list[str] = []

    def walk(node: ET.Element) -> None:
        tag = node.tag.rsplit("}", 1)[-1]
        if tag in _SKIP_JATS_TAGS:
            if node.tail:
                parts.append(node.tail)
            return
        if tag in _BLOCK_JATS_TAGS:
            parts.append(" ")
        if node.text:
            parts.append(node.text)
        for child in node:
            walk(child)
        if tag in _BLOCK_JATS_TAGS:
            parts.append(" ")
        if node.tail:
            parts.append(node.tail)

    walk(element)
    return collapse_whitespace("".join(parts))


def _jats_article(root: ET.Element) -> ET.Element:
    if root.tag.rsplit("}", 1)[-1] == "article":
        return root
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] == "article":
            return element
    raise PaperLookupInputError("JATS payload has no article element")


def _first_descendant(element: ET.Element, tag: str) -> ET.Element | None:
    return next((node for node in element.iter() if node.tag.rsplit("}", 1)[-1] == tag), None)


def _jats_metadata(article: ET.Element) -> dict[str, Any]:
    metadata: dict[str, Any] = {"abstract": None, "authors": [], "doi": None, "pmcid": None, "pmid": None, "title": None}
    front = next((node for node in article if node.tag.rsplit("}", 1)[-1] == "front"), None)
    if front is None:
        return metadata
    title = _first_descendant(front, "article-title")
    if title is not None:
        metadata["title"] = _jats_text(title) or None
    abstract = _first_descendant(front, "abstract")
    if abstract is not None:
        metadata["abstract"] = _jats_text(abstract) or None
    for node in front.iter():
        if node.tag.rsplit("}", 1)[-1] != "article-id":
            continue
        identifier = collapse_whitespace(node.text)
        kind = node.get("pub-id-type")
        field = {"doi": "doi", "pmcid": "pmcid", "pmc": "pmcid", "pmid": "pmid"}.get(kind or "")
        if field and metadata[field] is None and identifier:
            metadata[field] = identifier
    for contributor in front.iter():
        if contributor.tag.rsplit("}", 1)[-1] != "contrib":
            continue
        given = _first_descendant(contributor, "given-names")
        surname = _first_descendant(contributor, "surname")
        name = " ".join(part for part in (_jats_text(given) if given is not None else "", _jats_text(surname) if surname is not None else "") if part)
        if name:
            metadata["authors"].append(name)
    return metadata


def normalize_jats(xml_text: str) -> dict[str, Any]:
    """Normalize readable JATS body text; bodyless XML remains metadata-only."""
    try:
        article = _jats_article(ET.fromstring(xml_text))
    except ET.ParseError as error:
        raise PaperLookupInputError(f"JATS payload is not XML: {error}") from error
    metadata = _jats_metadata(article)
    body = next((node for node in article if node.tag.rsplit("}", 1)[-1] == "body"), None)
    if body is None:
        return {
            "full_text_available": False,
            "metadata": metadata,
            "reason": "JATS article has no body; metadata must not be represented as full text",
            "sections": [],
        }
    top_level = [node for node in body if node.tag.rsplit("}", 1)[-1] == "sec"]
    if not top_level:
        text = _jats_text(body)
        sections = [{"sec_type": None, "text": text, "title": ""}] if text else []
    else:
        sections = []
        for section in top_level:
            title = next((node for node in section if node.tag.rsplit("}", 1)[-1] == "title"), None)
            sections.append({"sec_type": section.get("sec-type"), "text": _jats_text(section), "title": _jats_text(title) if title is not None else ""})
    return {
        "full_text_available": True,
        "metadata": metadata,
        "section_count": len(sections),
        "sections": sections,
        "word_count": sum(len(section["text"].split()) for section in sections),
    }


def reconcile_pagination(payload: Any) -> dict[str, Any]:
    """Reconcile recorded pages without fetching or guessing continuation state."""
    fixture = _require_mapping(payload, "pagination fixture")
    if fixture.get("error") or fixture.get("errCode"):
        detail = fixture.get("error") or fixture.get("errMsg") or fixture.get("errCode")
        raise PaperLookupInputError(f"HTTP-200 endpoint error payload: {detail}")
    pages = fixture.get("pages")
    if not isinstance(pages, list) or not pages:
        raise PaperLookupInputError("pagination fixture requires a non-empty pages list")
    expected = fixture.get("expected_total")
    if expected is not None and (not isinstance(expected, int) or isinstance(expected, bool) or expected < 0):
        raise PaperLookupInputError("expected_total must be a non-negative integer or null")
    records: list[Any] = []
    notes: list[str] = []
    previous_next_state: Any = None
    stopped_before_termination = False
    for index, page in enumerate(pages):
        page_data = _require_mapping(page, f"page {index}")
        if page_data.get("error") or page_data.get("errCode"):
            detail = page_data.get("error") or page_data.get("errMsg") or page_data.get("errCode")
            raise PaperLookupInputError(f"HTTP-200 endpoint error payload on page {index}: {detail}")
        if (
            index
            and previous_next_state is not None
            and "request_state" in page_data
            and page_data["request_state"] != previous_next_state
        ):
            raise PaperLookupInputError(
                f"page {index} request_state does not match page {index - 1} next_state"
            )
        page_records = page_data.get("records")
        if not isinstance(page_records, list):
            raise PaperLookupInputError(f"page {index} records must be a list")
        reported_count = page_data.get("reported_count", len(page_records))
        if reported_count != len(page_records):
            raise PaperLookupInputError(f"page {index} reported_count does not match records length")
        records.extend(page_records)
        previous_next_state = page_data.get("next_state")
        if previous_next_state is not None and index == len(pages) - 1:
            stopped_before_termination = True
            notes.append("recorded fixture stopped before endpoint exhaustion")
    retrieved = len(records)
    complete = not stopped_before_termination and (expected is None or retrieved == expected)
    result: dict[str, Any] = {
        "complete": complete,
        "expected_total": expected,
        "pages_fetched": len(pages),
        "records": records,
        "retrieved_total": retrieved,
        "stopped_before_termination": stopped_before_termination,
    }
    if expected is None:
        result["expected_total_note"] = "endpoint did not report a total; completeness cannot be established from count"
    elif retrieved != expected:
        result["shortfall"] = expected - retrieved
        result["shortfall_reason"] = "recorded pages do not reconcile with the endpoint-reported total"
    elif stopped_before_termination:
        result["shortfall_reason"] = "endpoint supplied a continuation state, so termination was not observed"
    if notes:
        result["notes"] = notes
    return result


def load_json_text(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise PaperLookupInputError(f"payload is not JSON: {error}") from error
