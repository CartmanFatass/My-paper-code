from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from tools.research.paper_lookup.fetch import fetch_named_endpoint
from tools.research.paper_lookup.normalizers import (
    PaperLookupInputError,
    normalize_arxiv_atom,
    normalize_jats,
    normalize_openalex,
    reconcile_pagination,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = REPO_ROOT / "tools" / "research" / "paper_lookup" / "cli.py"
ARXIV_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom"
      xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
  <title>search_query=all:attention</title><opensearch:totalResults>1</opensearch:totalResults>
  <link rel="self" href="https://export.arxiv.org/api/query?search_query=all:attention"/>
  <entry>
    <id>https://arxiv.org/abs/1706.03762v7</id><title> Attention\n Is All You Need </title>
    <summary> A   representative\nabstract. </summary><published>2017-06-12</published>
    <author><name>Alice</name></author><author><name>Bob</name></author>
    <category term="cs.CL"/><arxiv:primary_category term="cs.CL"/><arxiv:doi>10.1/example</arxiv:doi>
    <link rel="alternate" type="text/html" href="https://arxiv.org/abs/1706.03762"/>
    <link rel="related" type="application/pdf" href="https://arxiv.org/pdf/1706.03762"/>
  </entry>
</feed>"""


def test_arxiv_atom_normalizes_versioned_identifier_and_links() -> None:
    result = normalize_arxiv_atom(ARXIV_FIXTURE)

    assert result["total_results"] == 1
    assert result["returned"] == 1
    assert result["entries"] == [
        {
            "abstract": "A representative abstract.",
            "abstract_url": "https://arxiv.org/abs/1706.03762",
            "arxiv_id": "1706.03762",
            "arxiv_id_versioned": "1706.03762v7",
            "authors": ["Alice", "Bob"],
            "categories": ["cs.CL"],
            "doi": "10.1/example",
            "pdf_url": "https://arxiv.org/pdf/1706.03762",
            "primary_category": "cs.CL",
            "published": "2017-06-12",
            "title": "Attention Is All You Need",
            "updated": None,
            "version": "7",
        }
    ]


def test_arxiv_http_200_error_feed_is_not_metadata() -> None:
    error_feed = ARXIV_FIXTURE.replace("Attention\n Is All You Need", "Error").replace(
        "A   representative\nabstract.", "bad query"
    )

    try:
        normalize_arxiv_atom(error_feed)
    except PaperLookupInputError as error:
        assert "HTTP-200 error feed" in str(error)
    else:
        raise AssertionError("arXiv Error feed must be rejected")


def test_openalex_inverted_abstract_retains_collisions_and_reports_gaps() -> None:
    result = normalize_openalex(
        {
            "id": "https://openalex.org/W1",
            "doi": "https://doi.org/10.1/example",
            "title": "Example work",
            "publication_year": 2024,
            "abstract_inverted_index": {"alpha": [0, 2], "beta": [1], "gamma": [2]},
        }
    )

    work = result["works"][0]
    assert work["abstract"] == "alpha beta alpha gamma"
    assert work["abstract_word_count"] == 4
    assert work["abstract_warnings"] == ["1 position(s) have multiple tokens; retained index order"]


def test_jats_body_is_text_but_bodyless_jats_is_metadata_only() -> None:
    with_body = normalize_jats(
        """<article><front><article-meta><title-group><article-title>Sample</article-title></title-group>
        <article-id pub-id-type="doi">10.1/sample</article-id></article-meta></front>
        <body><sec sec-type="methods"><title>Methods</title><p>Measured <italic>carefully</italic>.</p></sec></body></article>"""
    )
    metadata_only = normalize_jats(
        """<article><front><article-meta><title-group><article-title>Metadata only</article-title>
        </title-group></article-meta></front></article>"""
    )

    assert with_body["full_text_available"] is True
    assert with_body["sections"] == [{"sec_type": "methods", "text": "Methods Measured carefully.", "title": "Methods"}]
    assert metadata_only["full_text_available"] is False
    assert metadata_only["metadata"]["title"] == "Metadata only"
    assert metadata_only["sections"] == []


def test_pagination_reconciles_shortfall_and_surfaces_false_success() -> None:
    shortfall = reconcile_pagination(
        {"expected_total": 3, "pages": [{"records": [{"id": "a"}, {"id": "b"}], "reported_count": 2}]}
    )
    assert shortfall["complete"] is False
    assert shortfall["shortfall"] == 1
    complete = reconcile_pagination(
        {
            "expected_total": 2,
            "pages": [
                {"next_state": "cursor-2", "records": [{"id": "a"}], "reported_count": 1},
                {"request_state": "cursor-2", "records": [{"id": "b"}], "reported_count": 1},
            ],
        }
    )
    assert complete["complete"] is True
    assert complete["records"] == [{"id": "a"}, {"id": "b"}]

    try:
        reconcile_pagination({"pages": [{"records": [], "reported_count": 0, "errCode": "invalid query"}]})
    except PaperLookupInputError as error:
        assert "HTTP-200 endpoint error payload" in str(error)
    else:
        raise AssertionError("embedded endpoint errors must be surfaced")


def test_network_boundary_requires_explicit_opt_in_before_request() -> None:
    try:
        fetch_named_endpoint("arxiv", {"id_list": "1706.03762"})
    except PaperLookupInputError as error:
        assert "network access is disabled" in str(error)
    else:
        raise AssertionError("a request without explicit opt-in must not run")


def test_cli_file_input_emits_deterministic_local_tool_envelope() -> None:
    with tempfile.TemporaryDirectory() as directory:
        fixture = Path(directory) / "arxiv.xml"
        fixture.write_text(ARXIV_FIXTURE, encoding="utf-8")
        first = subprocess.run(
            [sys.executable, str(CLI), "arxiv", str(fixture)],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        second = subprocess.run(
            [sys.executable, str(CLI), "arxiv", str(fixture)],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    assert first.stdout == second.stdout
    packet = json.loads(first.stdout)
    assert packet["schema_version"] == 1
    assert packet["tool"] == "paper_lookup"
    assert packet["network_used"] is False
    assert packet["scientific_effect"] == "none"
    assert packet["result"]["entries"][0]["arxiv_id"] == "1706.03762"
