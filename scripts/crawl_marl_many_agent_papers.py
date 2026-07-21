#!/usr/bin/env python3
"""Build a conference-verified MARL paper index with official code links.

The crawler deliberately separates three questions:

1. Was the paper published at a configured conference in the requested years?
2. Is the paper about MARL / many-agent RL rather than merely mentioning agents?
3. Does Papers with Code identify an official implementation?

ICLR, ICML, NeurIPS, AAMAS, and IJCAI metadata comes from their official
proceedings. AAAI uses an exact OpenAlex conference-source filter whose records
link to the official OJS/DOI copies. Code metadata comes from official
proceedings code/software links and the public Papers-with-Code archive exposed
through the Hugging Face Dataset Viewer API. Only author/official code rows are
written to the primary output.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from http.client import IncompleteRead, RemoteDisconnected
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


OPENALEX_API = "https://api.openalex.org/works"
HF_FILTER_API = "https://datasets-server.huggingface.co/filter"
PWC_DATASET = "pwc-archive/links-between-paper-and-code"

OPENALEX_CONFERENCES = {
    "ICLR": "S4306419637",
    "ICML": "S4306419644",
    "NeurIPS": "S4306420609",
    "AAAI": "S4210191458",
    "IJCAI": "S4306419999",
}

AAMAS_PROCEEDINGS = {
    2023: "https://www.ifaamas.org/Proceedings/aamas2023/forms/contents.htm",
    2024: "https://www.ifaamas.org/Proceedings/aamas2024/forms/contents.htm",
    2025: "https://www.ifaamas.org/Proceedings/aamas2025/forms/contents.htm",
}

ICLR_PROCEEDINGS = {
    2023: "https://iclr.cc/virtual/2023/papers.html",
    2024: "https://proceedings.iclr.cc/paper_files/paper/2024",
    2025: "https://proceedings.iclr.cc/paper_files/paper/2025",
}

NEURIPS_PROCEEDINGS = {
    year: f"https://proceedings.neurips.cc/papers/{year}"
    for year in (2023, 2024, 2025)
}

ICML_PMLR_VOLUMES = {
    2023: "https://proceedings.mlr.press/v202/",
    2024: "https://proceedings.mlr.press/v235/",
    2025: "https://proceedings.mlr.press/v267/",
}

IJCAI_PROCEEDINGS = {
    year: f"https://www.ijcai.org/proceedings/{year}/"
    for year in (2023, 2024, 2025)
}

# Strong phrases identify the field itself.  The secondary patterns retain
# algorithm papers whose titles use the method family rather than the MARL
# acronym.  Abstract matching is required for the more permissive patterns.
STRONG_PATTERNS = [
    re.compile(r"\bmulti[ -]?agent reinforcement learning\b", re.I),
    re.compile(r"\bmultiagent reinforcement learning\b", re.I),
    re.compile(r"\bmany[ -]?agent reinforcement learning\b", re.I),
    re.compile(r"\bmean[ -]?field (?:multi[ -]?agent )?reinforcement learning\b", re.I),
    re.compile(r"\breinforcement learning.{0,80}\b(?:many[ -]?agent|mean[ -]?field|large[ -]?population)\b", re.I | re.S),
    re.compile(r"\bMARL\b"),
]

ALGORITHM_PATTERNS = [
    re.compile(r"\bmulti[ -]?agent (?:actor[ -]?critic|q[ -]?learning|policy (?:gradient|optimization)|value decomposition)\b", re.I),
    re.compile(r"\bcooperative multi[ -]?agent (?:learning|exploration|coordination|communication|credit assignment)\b", re.I),
    re.compile(r"\bdecentralized (?:multi[ -]?agent )?(?:PPO|policy optimization|reinforcement learning)\b", re.I),
    re.compile(r"\b(?:many[ -]?agent|large[ -]?population|massively multi[ -]?agent).{0,100}\b(?:RL|reinforcement learning)\b", re.I | re.S),
]

EXCLUSION_PATTERNS = [
    re.compile(r"\bsurvey\b", re.I),
    re.compile(r"\breview of\b", re.I),
    re.compile(r"\bdoctoral consortium\b", re.I),
    re.compile(r"\bstudent abstract\b", re.I),
    re.compile(r"\bextended abstract\b", re.I),
]

MANY_AGENT_SCOPE_PATTERN = re.compile(
    r"\b(?:many[ -]?agent|mean[ -]?field|large[ -]?population|massively multi[ -]?agent|"
    r"scal(?:able|ability|ing)|agent (?:number|population|grouping)|permutation (?:invariant|equivariant)|"
    r"information aggregation|networked multi[ -]?agent|swarm)\b",
    re.I,
)


@dataclass(frozen=True)
class Paper:
    title: str
    conference: str
    year: int
    authors: str
    paper_landing_url: str
    paper_pdf_url: str
    doi: str
    discovery_source: str
    match_reason: str


@dataclass(frozen=True)
class CodeLink:
    repo_url: str
    mentioned_in_paper: bool
    mentioned_in_github: bool
    framework: str
    paperswithcode_url: str
    evidence_source: str = "paperswithcode"


def request_json(url: str, *, attempts: int = 6, timeout: int = 45) -> dict[str, Any]:
    for attempt in range(attempts):
        try:
            req = Request(url, headers={"User-Agent": "HMASD-MARL-literature-index/1.0"})
            with urlopen(req, timeout=timeout) as response:
                return json.load(response)
        except HTTPError as exc:
            retryable = exc.code in {429, 500, 502, 503, 504}
            if not retryable or attempt + 1 == attempts:
                raise
            retry_after = exc.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else min(2 ** attempt, 20)
            time.sleep(delay)
        except (URLError, TimeoutError, IncompleteRead, RemoteDisconnected, ConnectionError, OSError):
            if attempt + 1 == attempts:
                raise
            time.sleep(min(2 ** attempt, 20))
    raise RuntimeError("unreachable")


def request_text(url: str, *, attempts: int = 5, timeout: int = 45) -> str:
    for attempt in range(attempts):
        try:
            req = Request(url, headers={"User-Agent": "HMASD-MARL-literature-index/1.0"})
            with urlopen(req, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except (HTTPError, URLError, TimeoutError, IncompleteRead, RemoteDisconnected, ConnectionError, OSError):
            if attempt + 1 == attempts:
                raise
            time.sleep(min(2 ** attempt, 20))
    raise RuntimeError("unreachable")


def normalize_title(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_external_url(value: str) -> str:
    value = html.unescape(value or "").strip()
    value = re.sub(r"^https:\s*//", "https://", value, flags=re.I)
    value = re.sub(r"^http:\s*//", "http://", value, flags=re.I)
    return value.rstrip(".,;:!?)]}\\")


def is_repository_url(value: str) -> bool:
    return bool(re.match(r"https?://(?:www\.)?(?:github\.com|gitlab\.com|bitbucket\.org)/", value, re.I))


def inverted_abstract(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    words: list[tuple[int, str]] = []
    for token, positions in index.items():
        words.extend((position, token) for position in positions)
    words.sort()
    return " ".join(token for _, token in words)


def match_reason(title: str, abstract: str = "", *, aamas_marl_session: bool = False) -> str:
    if any(pattern.search(title) for pattern in EXCLUSION_PATTERNS):
        return ""
    text = f"{title}\n{abstract}"
    for pattern in STRONG_PATTERNS:
        if pattern.search(title):
            return f"title:{pattern.pattern}"
    if aamas_marl_session:
        return "official_aamas_marl_session"
    for pattern in STRONG_PATTERNS:
        if pattern.search(text):
            return f"abstract:{pattern.pattern}"
    for pattern in ALGORITHM_PATTERNS:
        if pattern.search(text):
            return f"algorithm_family:{pattern.pattern}"
    return ""


def venue_location(work: dict[str, Any], source_id: str) -> dict[str, Any]:
    suffix = f"/{source_id}"
    for location in work.get("locations") or []:
        source = location.get("source") or {}
        if str(source.get("id", "")).endswith(suffix):
            return location
    return work.get("primary_location") or {}


def openalex_papers(
    conference: str,
    years: list[int],
    *,
    max_pages: int | None = None,
) -> list[Paper]:
    source_id = OPENALEX_CONFERENCES[conference]
    start, end = min(years), max(years)
    cursor = "*"
    page = 0
    papers: list[Paper] = []
    seen: set[str] = set()

    while cursor:
        params = {
            # OpenAlex's AAAI source contains the whole proceedings.  The
            # field phrase is used only as an index prefilter; the stricter
            # local title/abstract patterns still decide inclusion.
            "search": "multi-agent reinforcement learning",
            "filter": (
                f"from_publication_date:{start}-01-01,"
                f"to_publication_date:{end}-12-31,"
                f"locations.source.id:{source_id}"
            ),
            # A page can exceed 2 MB for AAAI. Incomplete TLS responses are
            # retried by request_json, so the larger page remains worthwhile.
            "per-page": 200,
            "cursor": cursor,
            "select": (
                "id,doi,title,publication_year,publication_date,primary_location,"
                "best_oa_location,locations,authorships,abstract_inverted_index"
            ),
        }
        payload = request_json(f"{OPENALEX_API}?{urlencode(params)}")
        page += 1
        for work in payload.get("results", []):
            year = int(work.get("publication_year") or 0)
            if year not in years:
                continue
            title = normalize_title(work.get("title") or "")
            abstract = inverted_abstract(work.get("abstract_inverted_index"))
            reason = match_reason(title, abstract)
            key = normalize_title(title).casefold()
            if not reason or not key or key in seen:
                continue
            seen.add(key)
            location = venue_location(work, source_id)
            fallback = work.get("best_oa_location") or work.get("primary_location") or {}
            authors = "; ".join(
                (entry.get("author") or {}).get("display_name", "")
                for entry in work.get("authorships") or []
                if (entry.get("author") or {}).get("display_name")
            )
            papers.append(
                Paper(
                    title=title,
                    conference=conference,
                    year=year,
                    authors=authors,
                    paper_landing_url=(
                        location.get("landing_page_url")
                        or fallback.get("landing_page_url")
                        or work.get("doi")
                        or ""
                    ),
                    paper_pdf_url=location.get("pdf_url") or fallback.get("pdf_url") or "",
                    doi=work.get("doi") or "",
                    discovery_source="OpenAlex conference source",
                    match_reason=reason,
                )
            )
        cursor = (payload.get("meta") or {}).get("next_cursor")
        if page % 10 == 0 or not cursor:
            print(f"  {conference}: page {page}, retained {len(papers)} candidates", flush=True)
        if max_pages is not None and page >= max_pages:
            break
        time.sleep(0.12)
    return papers


def strip_tags(value: str) -> str:
    value = re.sub(r"(?is)<[^>]+>", " ", value)
    return normalize_title(value)


def aamas_papers(year: int) -> list[Paper]:
    contents_url = AAMAS_PROCEEDINGS[year]
    page = request_text(contents_url)
    header_pattern = re.compile(r"(?is)Session\s+[A-Z0-9]+\s*:\s*([^<]+)")
    headers = [(match.start(), strip_tags(match.group(0))) for match in header_pattern.finditer(page)]
    anchor_pattern = re.compile(
        r'(?is)<a\s+[^>]*href=["\'](?P<href>\.\./pdfs/p\d+\.pdf)["\'][^>]*>(?P<title>.*?)</a>'
    )
    papers: list[Paper] = []
    seen: set[str] = set()
    for match in anchor_pattern.finditer(page):
        title = strip_tags(match.group("title"))
        if not title:
            continue
        recent_header = ""
        for position, header in headers:
            if position > match.start():
                break
            recent_header = header
        in_marl_session = "multiagent reinforcement learning" in recent_header.casefold()
        reason = match_reason(title, aamas_marl_session=in_marl_session)
        key = title.casefold()
        if not reason or key in seen:
            continue
        seen.add(key)
        pdf_url = urljoin(contents_url, match.group("href"))
        papers.append(
            Paper(
                title=title,
                conference="AAMAS",
                year=year,
                authors="",
                paper_landing_url=contents_url,
                paper_pdf_url=pdf_url,
                doi="",
                discovery_source="official IFAAMAS proceedings",
                match_reason=reason,
            )
        )
    return papers


def iclr_or_neurips_papers(conference: str, year: int) -> list[Paper]:
    if conference == "ICLR":
        contents_url = ICLR_PROCEEDINGS[year]
    elif conference == "NeurIPS":
        contents_url = NEURIPS_PROCEEDINGS[year]
    else:
        raise ValueError(conference)
    page = request_text(contents_url)
    if conference == "ICLR" and year == 2023:
        virtual_pattern = re.compile(
            r'(?is)<li><a href=["\'](?P<href>/virtual/2023/poster/\d+)["\']>(?P<title>.*?)</a></li>'
        )
        papers: list[Paper] = []
        for match in virtual_pattern.finditer(page):
            title = strip_tags(match.group("title"))
            reason = match_reason(title)
            if not reason:
                continue
            landing_url = urljoin(contents_url, match.group("href"))
            papers.append(
                Paper(
                    title=title,
                    conference="ICLR",
                    year=year,
                    authors="",
                    paper_landing_url=landing_url,
                    paper_pdf_url="",
                    doi="",
                    discovery_source="official ICLR virtual proceedings",
                    match_reason=reason,
                )
            )
        return papers
    anchor_pattern = re.compile(
        r'(?is)<a\s+[^>]*title=["\']paper title["\'][^>]*href=["\'](?P<href>[^"\']+-Abstract-Conference\.html)["\'][^>]*>(?P<title>.*?)</a>'
    )
    papers: list[Paper] = []
    for match in anchor_pattern.finditer(page):
        title = strip_tags(match.group("title"))
        reason = match_reason(title)
        if not reason:
            continue
        landing_url = urljoin(contents_url, html.unescape(match.group("href")))
        pdf_url = landing_url.replace("/hash/", "/file/").replace(
            "-Abstract-Conference.html", "-Paper-Conference.pdf"
        )
        papers.append(
            Paper(
                title=title,
                conference=conference,
                year=year,
                authors="",
                paper_landing_url=landing_url,
                paper_pdf_url=pdf_url,
                doi="",
                discovery_source=f"official {conference} proceedings",
                match_reason=reason,
            )
        )
    return papers


def icml_papers(year: int) -> tuple[list[Paper], dict[str, list[CodeLink]]]:
    contents_url = ICML_PMLR_VOLUMES[year]
    page = request_text(contents_url)
    block_pattern = re.compile(r'(?is)<div class="paper">(?P<block>.*?)</div>')
    papers: list[Paper] = []
    code_map: dict[str, list[CodeLink]] = {}
    for match in block_pattern.finditer(page):
        block = match.group("block")
        title_match = re.search(r'(?is)<p class="title">(?P<title>.*?)</p>', block)
        if not title_match:
            continue
        title = strip_tags(title_match.group("title"))
        reason = match_reason(title)
        if not reason:
            continue
        author_match = re.search(r'(?is)<span class="authors">(?P<authors>.*?)</span>', block)
        authors = strip_tags(author_match.group("authors")) if author_match else ""
        links = [
            (normalize_external_url(href), strip_tags(label))
            for href, label in re.findall(r'(?is)<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', block)
        ]
        landing_url = next((href for href, label in links if label.casefold() == "abs"), "")
        pdf_url = next((href for href, label in links if "pdf" in label.casefold()), "")
        software_urls = [href for href, label in links if label.casefold() == "software"]
        papers.append(
            Paper(
                title=title,
                conference="ICML",
                year=year,
                authors=authors,
                paper_landing_url=landing_url,
                paper_pdf_url=pdf_url,
                doi="",
                discovery_source="official PMLR proceedings",
                match_reason=reason,
            )
        )
        if software_urls:
            code_map[title] = [
                CodeLink(
                    repo_url=normalize_external_url(url),
                    mentioned_in_paper=True,
                    mentioned_in_github=False,
                    framework="",
                    paperswithcode_url="",
                    evidence_source="official_proceedings_software",
                )
                for url in dict.fromkeys(software_urls)
            ]
    return papers, code_map


def ijcai_papers(year: int) -> list[Paper]:
    contents_url = IJCAI_PROCEEDINGS[year]
    page = request_text(contents_url)
    block_pattern = re.compile(
        r'(?is)<div id="paper\d+" class="paper_wrapper">(?P<block>.*?)(?=<div id="paper\d+" class="paper_wrapper">|$)'
    )
    papers: list[Paper] = []
    for match in block_pattern.finditer(page):
        block = match.group("block")
        title_match = re.search(r'(?is)<div class="title">(?P<title>.*?)</div>', block)
        if not title_match:
            continue
        title = strip_tags(title_match.group("title"))
        reason = match_reason(title)
        if not reason:
            continue
        author_match = re.search(r'(?is)<div class="authors">(?P<authors>.*?)</div>', block)
        authors = strip_tags(author_match.group("authors")) if author_match else ""
        pdf_match = re.search(r'(?is)<a href="(?P<href>\d+\.pdf)">PDF</a>', block)
        details_match = re.search(r'(?is)<a href="(?P<href>/proceedings/\d+/\d+)">\s*Details</a>', block)
        pdf_url = urljoin(contents_url, pdf_match.group("href")) if pdf_match else ""
        landing_url = urljoin(contents_url, details_match.group("href")) if details_match else contents_url
        papers.append(
            Paper(
                title=title,
                conference="IJCAI",
                year=year,
                authors=authors,
                paper_landing_url=landing_url,
                paper_pdf_url=pdf_url,
                doi="",
                discovery_source="official IJCAI proceedings",
                match_reason=reason,
            )
        )
    return papers


def pwc_official_code(title: str) -> list[CodeLink]:
    escaped = title.replace("'", "''")
    where = f'"paper_title"=\'{escaped}\' AND "is_official"=true'
    params = {
        "dataset": PWC_DATASET,
        "config": "default",
        "split": "train",
        "where": where,
        "offset": 0,
        "length": 100,
    }
    payload = request_json(f"{HF_FILTER_API}?{urlencode(params)}", attempts=7, timeout=60)
    results: list[CodeLink] = []
    seen: set[str] = set()
    for item in payload.get("rows") or []:
        row = item.get("row") or {}
        if normalize_title(row.get("paper_title", "")).casefold() != normalize_title(title).casefold():
            continue
        repo_url = normalize_external_url(row.get("repo_url") or "")
        if not row.get("is_official") or not repo_url or repo_url in seen:
            continue
        seen.add(repo_url)
        results.append(
            CodeLink(
                repo_url=repo_url,
                mentioned_in_paper=bool(row.get("mentioned_in_paper")),
                mentioned_in_github=bool(row.get("mentioned_in_github")),
                framework=row.get("framework") or "",
                paperswithcode_url=row.get("paper_url") or "",
            )
        )
    return results


def proceedings_page_code(paper: Paper) -> list[CodeLink]:
    if paper.conference not in {"ICLR", "NeurIPS", "IJCAI"} or not paper.paper_landing_url:
        return []
    page = html.unescape(request_text(paper.paper_landing_url))
    url_pattern = re.compile(
        r'https?://(?:www\.)?(?:github\.com|gitlab\.com|bitbucket\.org)/[^\s<>"\']+',
        re.I,
    )
    urls: list[str] = []
    for match in url_pattern.finditer(page):
        url = normalize_external_url(match.group(0))
        if "github.com/google/safevalues" in url.casefold():
            continue
        if url not in urls:
            urls.append(url)
    return [
        CodeLink(
            repo_url=url,
            mentioned_in_paper=True,
            mentioned_in_github=False,
            framework="",
            paperswithcode_url="",
            evidence_source="official_proceedings_page",
        )
        for url in urls
    ]


def refresh_direct_codes(paper: Paper, existing: list[CodeLink]) -> list[CodeLink]:
    additions = proceedings_page_code(paper)
    kept_existing: list[CodeLink] = []
    for code in existing:
        normalized_code = CodeLink(
            repo_url=normalize_external_url(code.repo_url),
            mentioned_in_paper=code.mentioned_in_paper,
            mentioned_in_github=code.mentioned_in_github,
            framework=code.framework,
            paperswithcode_url=code.paperswithcode_url,
            evidence_source=code.evidence_source,
        )
        if code.evidence_source == "official_proceedings_software" and not is_repository_url(normalized_code.repo_url):
            try:
                page = html.unescape(request_text(normalized_code.repo_url))
                resolved = []
                for match in re.finditer(
                    r'https?://(?:www\.)?(?:github\.com|gitlab\.com|bitbucket\.org)/[^\s<>"\']+',
                    page,
                    re.I,
                ):
                    url = normalize_external_url(match.group(0))
                    if "github.com/google/safevalues" in url.casefold():
                        continue
                    resolved.append(
                        CodeLink(
                            repo_url=url,
                            mentioned_in_paper=True,
                            mentioned_in_github=False,
                            framework=code.framework,
                            paperswithcode_url=code.paperswithcode_url,
                            evidence_source="official_proceedings_software",
                        )
                    )
                if resolved:
                    additions.extend(resolved)
                    continue
            except Exception:
                pass
        kept_existing.append(normalized_code)
    return merge_code_links(kept_existing, additions)


def lookup_codes(paper: Paper) -> list[CodeLink]:
    direct: list[CodeLink] = []
    try:
        direct = proceedings_page_code(paper)
    except Exception:
        # Papers with Code remains an independent fallback.  If it also fails,
        # let that error reach the caller so the title is reported explicitly.
        direct = []
    try:
        archive = pwc_official_code(paper.title)
    except Exception:
        if direct:
            archive = []
        else:
            raise
    merged: list[CodeLink] = []
    seen: set[str] = set()
    for code in [*direct, *archive]:
        normalized = code.repo_url.rstrip("/").casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        merged.append(code)
    return merged


def deduplicate(papers: Iterable[Paper]) -> list[Paper]:
    best: dict[tuple[str, int], Paper] = {}
    for paper in papers:
        key = (paper.title.casefold(), paper.year)
        current = best.get(key)
        if current is None:
            best[key] = paper
            continue
        # Prefer records with a direct conference PDF and populated authors.
        old_score = bool(current.paper_pdf_url) * 2 + bool(current.authors)
        new_score = bool(paper.paper_pdf_url) * 2 + bool(paper.authors)
        if new_score > old_score:
            best[key] = paper
    return sorted(best.values(), key=lambda item: (item.year, item.conference, item.title.casefold()))


def load_existing_outputs(output_dir: Path) -> tuple[list[Paper], dict[str, list[CodeLink]]]:
    matched_path = output_dir / "papers_with_official_code.csv"
    unmatched_path = output_dir / "candidates_without_official_code.csv"
    if not matched_path.exists() or not unmatched_path.exists():
        raise FileNotFoundError("refresh mode requires both existing CSV outputs")
    papers: list[Paper] = []
    code_map: dict[str, list[CodeLink]] = {}
    with matched_path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            paper = Paper(
                title=row["title"],
                conference=row["conference"],
                year=int(row["year"]),
                authors=row["authors"],
                paper_landing_url=row["paper_landing_url"],
                paper_pdf_url=row["paper_pdf_url"],
                doi=row["doi"],
                discovery_source=row["discovery_source"],
                match_reason=row["match_reason"],
            )
            papers.append(paper)
            evidence = row["code_evidence"]
            if evidence == "official proceedings software":
                source = "official_proceedings_software"
            elif evidence == "official proceedings code link":
                source = "official_proceedings_page"
            else:
                source = "paperswithcode"
            frameworks = row["frameworks"].split("; ") if row["frameworks"] else []
            code_map[paper.title] = [
                CodeLink(
                    repo_url=url,
                    mentioned_in_paper="mentioned_in_paper" in evidence or source.startswith("official_proceedings"),
                    mentioned_in_github="paper_linked_from_repo" in evidence,
                    framework=frameworks[0] if len(frameworks) == 1 else "",
                    paperswithcode_url=row["paperswithcode_url"],
                    evidence_source=source,
                )
                for url in row["code_urls"].split("; ")
                if url
            ]
    with unmatched_path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            papers.append(
                Paper(
                    title=row["title"],
                    conference=row["conference"],
                    year=int(row["year"]),
                    authors=row["authors"],
                    paper_landing_url=row["paper_landing_url"],
                    paper_pdf_url=row["paper_pdf_url"],
                    doi=row["doi"],
                    discovery_source=row["discovery_source"],
                    match_reason=row["match_reason"],
                )
            )
    return deduplicate(papers), code_map


def merge_code_links(existing: list[CodeLink], additions: list[CodeLink]) -> list[CodeLink]:
    merged: list[CodeLink] = []
    seen: set[str] = set()
    for code in [*additions, *existing]:
        normalized = code.repo_url.rstrip("/").casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        merged.append(code)
    return merged


def evidence_label(codes: list[CodeLink]) -> str:
    if any(code.evidence_source == "official_proceedings_software" for code in codes):
        return "official proceedings software"
    if any(code.evidence_source == "official_proceedings_page" for code in codes):
        return "official proceedings code link"
    if any(code.mentioned_in_paper for code in codes):
        return "official; mentioned_in_paper"
    if any(code.mentioned_in_github for code in codes):
        return "official; paper_linked_from_repo"
    return "official_by_paperswithcode"


def scope_label(paper: Paper) -> str:
    text = f"{paper.title}\n{paper.match_reason}"
    return "many_agent_scaling" if MANY_AGENT_SCOPE_PATTERN.search(text) else "MARL"


def write_outputs(
    output_dir: Path,
    papers: list[Paper],
    code_map: dict[str, list[CodeLink]],
    *,
    generated_at: str,
    conferences: list[str],
    years: list[int],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    matched = [paper for paper in papers if code_map.get(paper.title)]
    unmatched = [paper for paper in papers if not code_map.get(paper.title)]

    columns = [
        "year",
        "conference",
        "scope",
        "title",
        "authors",
        "paper_landing_url",
        "paper_pdf_url",
        "code_urls",
        "code_evidence",
        "frameworks",
        "paperswithcode_url",
        "doi",
        "discovery_source",
        "match_reason",
    ]
    with (output_dir / "papers_with_official_code.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for paper in matched:
            codes = code_map[paper.title]
            writer.writerow(
                {
                    "year": paper.year,
                    "conference": paper.conference,
                    "scope": scope_label(paper),
                    "title": paper.title,
                    "authors": paper.authors,
                    "paper_landing_url": paper.paper_landing_url,
                    "paper_pdf_url": paper.paper_pdf_url,
                    "code_urls": "; ".join(code.repo_url for code in codes),
                    "code_evidence": evidence_label(codes),
                    "frameworks": "; ".join(sorted({code.framework for code in codes if code.framework})),
                    "paperswithcode_url": next((code.paperswithcode_url for code in codes if code.paperswithcode_url), ""),
                    "doi": paper.doi,
                    "discovery_source": paper.discovery_source,
                    "match_reason": paper.match_reason,
                }
            )

    with (output_dir / "candidates_without_official_code.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(unmatched[0]).keys()) if unmatched else list(asdict(Paper("", "", 0, "", "", "", "", "", "")).keys()))
        writer.writeheader()
        for paper in unmatched:
            writer.writerow(asdict(paper))

    lines = [
        "# MARL and many-agent RL papers with official code (2023-2025)",
        "",
        f"Generated: `{generated_at}`",
        "",
        "Primary inclusion rule: a configured top-conference paper, a strong MARL/many-agent RL match, and at least one author code link from official proceedings or a Papers with Code implementation marked `official`.",
        "",
        f"Conferences: {', '.join(conferences)}",
        "",
        f"Years: {', '.join(map(str, years))}",
        "",
        f"Matched papers: **{len(matched)}**; relevant candidates without an official-code match: **{len(unmatched)}**.",
        "",
        f"Scope counts: **{sum(scope_label(paper) == 'MARL' for paper in matched)} MARL**; **{sum(scope_label(paper) == 'many_agent_scaling' for paper in matched)} many-agent scaling**.",
        "",
        "| Year | Conference | Scope | Paper | Original PDF | Official code | Evidence |",
        "|---:|---|---|---|---|---|---|",
    ]
    for paper in matched:
        codes = code_map[paper.title]
        paper_link = paper.paper_landing_url or paper.paper_pdf_url
        pdf_cell = f"[PDF]({paper.paper_pdf_url})" if paper.paper_pdf_url else "-"
        code_cell = "<br>".join(f"[code {index + 1}]({code.repo_url})" for index, code in enumerate(codes))
        safe_title = paper.title.replace("|", "\\|")
        lines.append(
            f"| {paper.year} | {paper.conference} | {scope_label(paper)} | [{safe_title}]({paper_link}) | {pdf_cell} | {code_cell} | {evidence_label(codes)} |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Code links come from official proceedings pages/PMLR Software fields or the Papers with Code archive's `official` label. This is not a claim that a repository is maintained or reproduces every reported number.",
            "- ICLR, ICML, NeurIPS, AAMAS, and IJCAI paper identity comes directly from their official proceedings. AAAI identity uses an exact OpenAlex conference-source filter whose links resolve to the official AAAI OJS/DOI copy.",
            "- The unmatched-candidate CSV is retained so missing code can be checked manually without weakening the primary code+paper list.",
            "",
        ]
    )
    (output_dir / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")

    metadata = {
        "generated_at": generated_at,
        "years": years,
        "conferences": conferences,
        "candidate_count": len(papers),
        "matched_official_code_count": len(matched),
        "unmatched_candidate_count": len(unmatched),
        "matched_scope_counts": {
            scope: sum(scope_label(paper) == scope for paper in matched)
            for scope in ("MARL", "many_agent_scaling")
        },
        "conference_sources": {
            "openalex_source_ids": {"AAAI": OPENALEX_CONFERENCES["AAAI"]} if "AAAI" in conferences else {},
            "aamas_official_proceedings": {str(year): AAMAS_PROCEEDINGS[year] for year in years if year in AAMAS_PROCEEDINGS and "AAMAS" in conferences},
            "iclr_official_proceedings": {str(year): ICLR_PROCEEDINGS[year] for year in years if year in ICLR_PROCEEDINGS and "ICLR" in conferences},
            "neurips_official_proceedings": {str(year): NEURIPS_PROCEEDINGS[year] for year in years if year in NEURIPS_PROCEEDINGS and "NeurIPS" in conferences},
            "icml_pmlr_proceedings": {str(year): ICML_PMLR_VOLUMES[year] for year in years if year in ICML_PMLR_VOLUMES and "ICML" in conferences},
            "ijcai_official_proceedings": {str(year): IJCAI_PROCEEDINGS[year] for year in years if year in IJCAI_PROCEEDINGS and "IJCAI" in conferences},
        },
        "code_source": PWC_DATASET,
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    parser.add_argument(
        "--conferences",
        nargs="+",
        choices=[*OPENALEX_CONFERENCES, "AAMAS"],
        default=["ICLR", "ICML", "NeurIPS", "AAMAS", "AAAI", "IJCAI"],
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/research/literature/marl_many_agent_2023_2025"),
    )
    parser.add_argument("--code-workers", type=int, default=8)
    parser.add_argument("--max-openalex-pages", type=int, default=None, help="Diagnostic limit; omit for a complete crawl.")
    parser.add_argument(
        "--refresh-proceedings-code",
        action="store_true",
        help="Reuse existing candidate CSVs and refresh direct code links from official proceedings pages.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    years = sorted(set(args.years))
    conferences = list(dict.fromkeys(args.conferences))
    unsupported_aamas = [year for year in years if year not in AAMAS_PROCEEDINGS]
    if "AAMAS" in conferences and unsupported_aamas:
        print(f"AAMAS proceedings URLs are not configured for: {unsupported_aamas}", file=sys.stderr)
        return 2

    if args.refresh_proceedings_code:
        papers, code_map = load_existing_outputs(args.output_dir)
        refresh_papers = [paper for paper in papers if paper.conference in {"ICLR", "ICML", "NeurIPS", "IJCAI"}]
        with ThreadPoolExecutor(max_workers=max(1, args.code_workers)) as executor:
            futures = {
                executor.submit(refresh_direct_codes, paper, code_map.get(paper.title, [])): paper
                for paper in refresh_papers
            }
            for completed, future in enumerate(as_completed(futures), start=1):
                paper = futures[future]
                try:
                    code_map[paper.title] = future.result()
                except Exception as exc:
                    print(f"Proceedings code refresh failed: {paper.title}: {exc}", file=sys.stderr)
                if completed % 25 == 0 or completed == len(refresh_papers):
                    print(f"Proceedings code refresh: {completed}/{len(refresh_papers)}", flush=True)
        generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        write_outputs(
            args.output_dir,
            papers,
            code_map,
            generated_at=generated_at,
            conferences=sorted({paper.conference for paper in papers}),
            years=sorted({paper.year for paper in papers}),
        )
        matched = sum(bool(code_map.get(paper.title)) for paper in papers)
        print(f"Wrote {matched} code+paper matches to {args.output_dir}", flush=True)
        return 0

    discovered: list[Paper] = []
    seeded_code_map: dict[str, list[CodeLink]] = {}
    for conference in conferences:
        print(f"Discovering {conference} {years[0]}-{years[-1]}...", flush=True)
        if conference == "AAMAS":
            for year in years:
                discovered.extend(aamas_papers(year))
        elif conference in {"ICLR", "NeurIPS"}:
            for year in years:
                discovered.extend(iclr_or_neurips_papers(conference, year))
        elif conference == "ICML":
            for year in years:
                papers, direct_codes = icml_papers(year)
                discovered.extend(papers)
                seeded_code_map.update(direct_codes)
        elif conference == "IJCAI":
            for year in years:
                discovered.extend(ijcai_papers(year))
        else:
            discovered.extend(
                openalex_papers(
                    conference,
                    years,
                    max_pages=args.max_openalex_pages,
                )
            )

    papers = deduplicate(discovered)
    print(f"Relevant candidates: {len(papers)}", flush=True)
    code_map: dict[str, list[CodeLink]] = dict(seeded_code_map)
    lookup_papers = [paper for paper in papers if paper.title not in code_map]
    with ThreadPoolExecutor(max_workers=max(1, args.code_workers)) as executor:
        futures = {executor.submit(lookup_codes, paper): paper for paper in lookup_papers}
        completed = 0
        for future in as_completed(futures):
            paper = futures[future]
            completed += 1
            try:
                code_map[paper.title] = future.result()
            except Exception as exc:  # retain crawl progress and report the exact title
                print(f"Code lookup failed: {paper.title}: {exc}", file=sys.stderr)
                code_map[paper.title] = []
            if completed % 25 == 0 or completed == len(lookup_papers):
                print(f"Code lookups: {completed}/{len(lookup_papers)}", flush=True)

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    write_outputs(
        args.output_dir,
        papers,
        code_map,
        generated_at=generated_at,
        conferences=conferences,
        years=years,
    )
    matched = sum(bool(code_map.get(paper.title)) for paper in papers)
    print(f"Wrote {matched} code+paper matches to {args.output_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
