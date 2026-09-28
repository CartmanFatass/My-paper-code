#!/usr/bin/env python3
"""Build a lightweight LLM index over the My-lib paper corpus (stdlib only).

Subcommands:
  catalog   deterministic catalog.jsonl + titles.tsv from the PDFs and the arXiv match file
  hints     one LLM "index hint" per paper via headless ``omp`` (resumable: hints/<id>.json)
  navigate  merged hints.jsonl, INDEX_BY_TOPIC.md, INDEX_BY_RELEVANCE.md and README.md
  all       catalog, hints, navigate

Hints locate papers; they are not evidence. The builder never modifies a PDF and writes only
under ``--out`` (plus omp's own state under ``--omp-cwd``).
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as _dt
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
MYLIB_ROOT = Path("/mnt/c/Projects/My-lib")
DEFAULT_CORPUS_ROOT = MYLIB_ROOT / ".local-formal-capture" / "corpus" / "papers"
DEFAULT_MATCHES_JSON = (
    MYLIB_ROOT / ".local-formal-capture" / ".local-acquisition" / "downloads" / "four-year-arxiv-matches.json"
)
DEFAULT_OUT = MYLIB_ROOT / ".local-llm-index"
DEFAULT_OMP_CWD = REPO_ROOT / "temp" / "directions" / "energy_relay_benchmark" / "scratch" / "mylib-index-20260928"

DEFAULT_MODEL = "gemini-3.8-flash"
DEFAULT_THINKING = "medium"
CALL_TIMEOUT_S = 120
TEXT_CHAR_LIMIT = 6000
RAW_KEEP_CHARS = 4000

ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")
ARXIV_FILE_RE = re.compile(r"^(?:arxiv-)?(?P<aid>\d{4}\.\d{4,5}(?:v\d+)?)\.pdf$")

# ---------------------------------------------------------------------------------------------
# Hint schema

MARL_SETTINGS = ("cooperative", "competitive", "mixed", "single-agent", "bandit", "theory-only", "other")
TOPICS = (
    "MARL", "hierarchical-RL", "options-skills", "credit-assignment", "communication", "exploration",
    "coordination-planning", "multi-robot-UAV", "offline-RL", "model-based", "world-models",
    "imitation-IRL", "safe-constrained-RL", "bandits", "theory", "LLM-agents", "representation",
    "generalization-transfer", "reward-design", "population-learning", "other",
)
CONFIDENCE = ("high", "medium", "low")
WORD_CAPS = {
    "problem_setting": 40,
    "method_summary": 60,
    "key_mechanism": 30,
    "hmasd_relevance_reason": 25,
    "one_line_hint": 30,
}
KEYWORD_MAX_WORDS = 6
HINT_KEYS = (
    "problem_setting", "method_summary", "key_mechanism", "mechanism_keywords", "marl_setting",
    "topics", "hmasd_relevance", "hmasd_relevance_reason", "one_line_hint", "confidence",
)

SYSTEM_PROMPT = (
    "You write index hints for a local library of machine-learning research papers. An index hint "
    "only helps a researcher decide whether to open a paper and which words to search for; it is "
    "not a review, not a rating of quality and not a summary of results. Use only the title, venue, "
    "abstract and first-pages text you are given. Do not state any claim, number, dataset, baseline "
    "or comparison that is not in that text; when the text is unclear, say less and lower the "
    "confidence. Output exactly one JSON object and nothing else: no markdown fences, no "
    "commentary, no reasoning."
)

USER_TEMPLATE = """Write an index hint for the paper below as ONE JSON object with exactly these keys:

"problem_setting": string, HARD LIMIT 40 words. The task/setting the paper addresses.
"method_summary": string, HARD LIMIT 60 words. What the method does, concretely.
"key_mechanism": string, HARD LIMIT 30 words. The one idea that makes the method work.
"mechanism_keywords": list of 3 to 8 short strings (each at most 6 words), specific technical terms a researcher would search for (names of algorithms, mechanisms, objectives), not generic words like "reinforcement learning".
"marl_setting": exactly one of: cooperative, competitive, mixed, single-agent, bandit, theory-only, other.
"topics": list of 2 to 6 distinct values, only from: MARL, hierarchical-RL, options-skills, credit-assignment, communication, exploration, coordination-planning, multi-robot-UAV, offline-RL, model-based, world-models, imitation-IRL, safe-constrained-RL, bandits, theory, LLM-agents, representation, generalization-transfer, reward-design, population-learning, other.
"hmasd_relevance": integer 0, 1, 2 or 3. Relevance to either theme (A) hierarchical multi-agent RL in which agents learn and coordinate skills/options/sub-policies, or (B) cooperative planning or path planning for UAV/drone swarms or multi-robot teams.
   3 = directly about theme A or theme B.
   2 = a close building block: cooperative MARL coordination, credit assignment or communication; single-agent hierarchical RL, skill discovery or options; multi-agent/multi-robot planning or path finding.
   1 = a general RL/MARL method that could be borrowed, but nothing specific to A or B.
   0 = no clear connection to A or B.
"hmasd_relevance_reason": string, HARD LIMIT 25 words. Why that relevance score.
"one_line_hint": string, HARD LIMIT 30 words. The line a researcher would grep for: setting + mechanism.
"confidence": one of high, medium, low (low if the given text is thin or garbled).

Word limits are hard limits: prefer fewer words. Every key must be present; add no other key.

PAPER
Title: {title}
Venue: {venue_year}
arXiv abstract (may be truncated): {abstract}
First-pages text (extracted, may be garbled, truncated to {char_limit} characters):
<<<
{text}
>>>
"""

RETRY_TEMPLATE = """

Your previous output was rejected for these reasons:
{errors}
Previous output (truncated):
<<<
{previous}
>>>
Return the corrected JSON object only."""


def prompt_version() -> str:
    material = "\x1e".join((SYSTEM_PROMPT, USER_TEMPLATE, RETRY_TEMPLATE, ",".join(TOPICS), ",".join(MARL_SETTINGS)))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:12]


def word_count(text: str) -> int:
    return len(text.split())


def validate_hint(obj: Any) -> List[str]:
    """Return a list of schema violations (empty when the hint is valid)."""
    errors: List[str] = []
    if not isinstance(obj, dict):
        return ["output is not a JSON object"]
    missing = [k for k in HINT_KEYS if k not in obj]
    extra = sorted(k for k in obj if k not in HINT_KEYS)
    if missing:
        errors.append("missing keys: " + ", ".join(missing))
    if extra:
        errors.append("unexpected keys: " + ", ".join(extra))
    for key, cap in WORD_CAPS.items():
        if key not in obj:
            continue
        value = obj[key]
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} must be a non-empty string")
        elif word_count(value) > cap:
            errors.append(f"{key} has {word_count(value)} words; hard limit is {cap}")
    if "mechanism_keywords" in obj:
        kws = obj["mechanism_keywords"]
        if not isinstance(kws, list) or not all(isinstance(k, str) and k.strip() for k in kws):
            errors.append("mechanism_keywords must be a list of non-empty strings")
        else:
            if not 3 <= len(kws) <= 8:
                errors.append(f"mechanism_keywords has {len(kws)} items; need 3 to 8")
            long_kws = [k for k in kws if word_count(k) > KEYWORD_MAX_WORDS]
            if long_kws:
                errors.append(f"mechanism_keywords items over {KEYWORD_MAX_WORDS} words: {long_kws}")
    if "marl_setting" in obj and obj["marl_setting"] not in MARL_SETTINGS:
        errors.append(f"marl_setting {obj['marl_setting']!r} not in {list(MARL_SETTINGS)}")
    if "topics" in obj:
        topics = obj["topics"]
        if not isinstance(topics, list) or not all(isinstance(t, str) for t in topics):
            errors.append("topics must be a list of strings")
        else:
            bad = [t for t in topics if t not in TOPICS]
            if bad:
                errors.append(f"topics not in the fixed vocabulary: {bad}")
            if len(set(topics)) != len(topics):
                errors.append("topics contain duplicates")
            if not 2 <= len(topics) <= 6:
                errors.append(f"topics has {len(topics)} items; need 2 to 6")
    if "hmasd_relevance" in obj:
        rel = obj["hmasd_relevance"]
        if isinstance(rel, bool) or not isinstance(rel, int) or not 0 <= rel <= 3:
            errors.append("hmasd_relevance must be an integer 0-3")
    if "confidence" in obj and obj["confidence"] not in CONFIDENCE:
        errors.append(f"confidence {obj['confidence']!r} not in {list(CONFIDENCE)}")
    return errors


def extract_json_object(text: str) -> Any:
    """Parse the model text as JSON, tolerating markdown fences and surrounding prose."""
    s = text.strip()
    fence = re.match(r"^```[A-Za-z0-9]*\s*\n(.*?)\n?```\s*$", s, re.S)
    if fence:
        s = fence.group(1).strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    start, end = s.find("{"), s.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object found in model output")
    return json.loads(s[start:end + 1])


# ---------------------------------------------------------------------------------------------
# omp NDJSON stream

class OmpError(Exception):
    def __init__(self, kind: str, detail: str, cost: float = 0.0):
        super().__init__(f"{kind}: {detail}")
        self.kind = kind
        self.detail = detail
        self.cost = cost


def parse_omp_ndjson(stdout: str) -> Dict[str, Any]:
    """Extract assistant text, cost and stop information from ``omp --mode json`` output.

    The assistant text is in the last ``message_end`` event whose ``message.role`` is
    ``assistant``; cost is summed over all assistant ``message_end`` events.
    """
    assistant: List[Dict[str, Any]] = []
    bad_lines = 0
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            bad_lines += 1
            continue
        if not isinstance(event, dict) or event.get("type") != "message_end":
            continue
        message = event.get("message") or {}
        if message.get("role") == "assistant":
            assistant.append(message)
    cost = 0.0
    for message in assistant:
        try:
            cost += float(((message.get("usage") or {}).get("cost") or {}).get("total") or 0.0)
        except (TypeError, ValueError):
            pass
    if not assistant:
        return {"found": False, "text": "", "cost": cost, "stop_reason": None, "error_message": None,
                "usage": None, "bad_lines": bad_lines, "model": None, "provider": None}
    last = assistant[-1]
    parts = [c.get("text", "") for c in (last.get("content") or [])
             if isinstance(c, dict) and c.get("type") == "text"]
    return {
        "found": True,
        "text": "".join(parts),
        "cost": cost,
        "stop_reason": last.get("stopReason"),
        "error_message": last.get("errorMessage"),
        "usage": last.get("usage"),
        "bad_lines": bad_lines,
        "model": last.get("model"),
        "provider": last.get("provider"),
    }


def classify_error_text(text: str) -> str:
    low = (text or "").lower()
    if re.search(r"\b429\b|rate.?limit|quota|resource.?exhausted|too many requests", low):
        return "rate_limit"
    if re.search(r"\b401\b|\b403\b|unauthori[sz]ed|auth|credential|api key|login|permission denied", low):
        return "auth"
    return ""


def omp_command(prompt: str, model: str, thinking: str, cwd: Path, timeout_s: int = CALL_TIMEOUT_S) -> List[str]:
    return [
        "timeout", "-k", "10", str(timeout_s),
        "omp", "-p", "--model", model, "--thinking", thinking,
        "--no-tools", "--no-session", "--no-extensions", "--no-skills", "--no-rules",
        "--no-title", "--no-lsp", "--system-prompt", SYSTEM_PROMPT,
        "--mode", "json", "--cwd", str(cwd), prompt,
    ]


def call_omp(prompt: str, model: str, thinking: str, cwd: Path, timeout_s: int = CALL_TIMEOUT_S) -> Dict[str, Any]:
    """One headless omp call. Returns the parsed stream or raises OmpError (infrastructure)."""
    cmd = omp_command(prompt, model, thinking, cwd, timeout_s)
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), stdin=subprocess.DEVNULL, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=timeout_s + 30)
    except subprocess.TimeoutExpired:
        raise OmpError("timeout", f"python backstop after {timeout_s + 30}s")
    parsed = parse_omp_ndjson(proc.stdout)
    stderr = (proc.stderr or "").strip()
    if proc.returncode == 124 or proc.returncode == 137:
        raise OmpError("timeout", f"omp exceeded {timeout_s}s (rc {proc.returncode})", parsed["cost"])
    if proc.returncode != 0:
        detail = f"rc {proc.returncode}: {stderr[-600:] or parsed.get('error_message') or 'no stderr'}"
        raise OmpError(classify_error_text(detail) or "exit", detail, parsed["cost"])
    if not parsed["found"]:
        detail = f"no assistant message_end; stderr: {stderr[-600:]}"
        raise OmpError(classify_error_text(detail) or "no_message", detail, parsed["cost"])
    if parsed["stop_reason"] not in (None, "stop", "end_turn", "length") or parsed["error_message"]:
        detail = f"stopReason {parsed['stop_reason']}: {parsed['error_message'] or ''}"[:800]
        raise OmpError(classify_error_text(detail) or "stop_error", detail, parsed["cost"])
    return parsed


# ---------------------------------------------------------------------------------------------
# Catalog

def pdf_info(path: Path) -> Dict[str, Any]:
    """Pages and Title from pdfinfo; nulls on any failure."""
    try:
        proc = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return {"pages": None, "title": None}
    if proc.returncode != 0:
        return {"pages": None, "title": None}
    pages = None
    title = None
    for line in proc.stdout.splitlines():
        if line.startswith("Pages:"):
            try:
                pages = int(line.split(":", 1)[1].strip())
            except ValueError:
                pages = None
        elif line.startswith("Title:"):
            title = line.split(":", 1)[1].strip() or None
    return {"pages": pages, "title": title}


def pdf_text(path: Path, first: int = 1, last: int = 2) -> str:
    try:
        proc = subprocess.run(["pdftotext", "-f", str(first), "-l", str(last), "-enc", "UTF-8", str(path), "-"],
                              capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout.decode("utf-8", errors="replace")


def first_page_title(text: str) -> Optional[str]:
    for line in text.splitlines():
        line = line.strip()
        if len(line) < 8 or line.lower().startswith("arxiv:"):
            continue
        return line
    return None


def load_matches(matches_json: Path) -> Dict[str, Dict[str, Any]]:
    data = json.loads(matches_json.read_text(encoding="utf-8"))
    by_arxiv: Dict[str, Dict[str, Any]] = {}
    for record in data.get("matches", []):
        arxiv = record.get("arxiv") or {}
        aid = arxiv.get("arxiv_id")
        if aid:
            by_arxiv.setdefault(aid, record)
    return by_arxiv


def arxiv_id_from_filename(name: str) -> Optional[str]:
    m = ARXIV_FILE_RE.match(name)
    return m.group("aid") if m else None


def catalog_id(record: Dict[str, Any]) -> str:
    """``official_id``, prefixed with ``<venue>-<year>-`` when it does not already carry it.

    NeurIPS/ICLR proceedings hash ids are reused across venues (e.g. the same hash names an
    ICLR 2024 and a NeurIPS 2023 paper), so a bare hash is not a unique key.
    """
    oid = str(record.get("official_id") or "")
    venue, year = record.get("venue"), record.get("year")
    if not venue or not year:
        return oid
    prefix = f"{str(venue).lower()}-{year}"
    return oid if oid.startswith(prefix) else f"{prefix}-{oid}"


def build_catalog_rows(pdf_paths: Iterable[Path], by_arxiv: Dict[str, Dict[str, Any]], corpus_root: Path,
                       info_fn=pdf_info, text_fn=pdf_text) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Join PDFs to arXiv match records. Pure except for ``info_fn``/``text_fn``."""
    rows: List[Dict[str, Any]] = []
    stats = {"pdfs": 0, "matched": 0, "loose": 0, "dir_id_mismatch": 0, "pages_null": 0, "bad_ids": []}
    for path in sorted(pdf_paths):
        stats["pdfs"] += 1
        info = info_fn(path)
        aid = arxiv_id_from_filename(path.name)
        record = by_arxiv.get(aid) if aid else None
        rel_parts = path.relative_to(corpus_root).parts
        try:
            size = path.stat().st_size
        except OSError:
            size = None
        if record is not None:
            stats["matched"] += 1
            arxiv = record.get("arxiv") or {}
            rid = record.get("official_id")
            if len(rel_parts) >= 2 and rel_parts[-2] != rid:
                stats["dir_id_mismatch"] += 1
            row = {
                "id": catalog_id(record),
                "official_id": rid,
                "venue": record.get("venue"),
                "year": record.get("year"),
                "title": record.get("title") or arxiv.get("title"),
                "arxiv_id": aid,
                "authors": arxiv.get("authors") or record.get("authors") or [],
                "published": arxiv.get("published") or None,
                "abstract": arxiv.get("summary") or None,
                "official_url": record.get("official_url"),
                "title_screen_hits": record.get("title_screen_hits"),
            }
        else:
            stats["loose"] += 1
            stem = aid or path.stem
            title = info.get("title") or first_page_title(text_fn(path, 1, 1))
            row = {
                "id": f"loose-{stem}", "official_id": None, "venue": None, "year": None, "title": title, "arxiv_id": None,
                "authors": None, "published": None, "abstract": None, "official_url": None,
                "title_screen_hits": None,
            }
        row["pdf_path"] = str(path.resolve())
        row["pdf_bytes"] = size
        row["pages"] = info.get("pages")
        if row["pages"] is None:
            stats["pages_null"] += 1
        if not row["id"] or not ID_RE.match(str(row["id"])):
            stats["bad_ids"].append(row["id"])
        rows.append(row)
    rows.sort(key=lambda r: str(r["id"]))
    ids = [r["id"] for r in rows]
    stats["duplicate_ids"] = sorted({i for i in ids if ids.count(i) > 1})
    stats["catalog_rows"] = len(rows)
    return rows, stats


def tsv_field(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"[\t\r\n]+", " ", str(value)).strip()


def atomic_write(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    atomic_write(path, "".join(json.dumps(r, ensure_ascii=False, sort_keys=False) + "\n" for r in rows))


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def cmd_catalog(args: argparse.Namespace) -> Dict[str, Any]:
    corpus_root = Path(args.corpus_root)
    pdfs = sorted(p for p in corpus_root.rglob("*.pdf") if p.is_file())
    by_arxiv = load_matches(Path(args.matches_json))
    infos: Dict[Path, Dict[str, Any]] = {}
    with cf.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for path, info in zip(pdfs, pool.map(pdf_info, pdfs)):
            infos[path] = info
    rows, stats = build_catalog_rows(pdfs, by_arxiv, corpus_root, info_fn=lambda p: infos[p])
    print(json.dumps({"catalog": {k: v for k, v in stats.items()}}, indent=1))
    if stats["bad_ids"] or stats["duplicate_ids"]:
        raise SystemExit("catalog ids are not unique filename-safe strings; refusing to write")
    if args.dry_run:
        return stats
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(out / "catalog.jsonl", rows)
    lines = ["id\tvenue\tyear\ttitle\tarxiv_id\n"]
    lines += ["\t".join(tsv_field(r[k]) for k in ("id", "venue", "year", "title", "arxiv_id")) + "\n" for r in rows]
    atomic_write(out / "titles.tsv", "".join(lines))
    return stats


# ---------------------------------------------------------------------------------------------
# Hints

def clean_text(text: str) -> str:
    text = text.replace("\x00", "").replace("\x0c", "\n")
    text = re.sub(r"[\x01-\x08\x0b\x0e-\x1f\x7f]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def venue_year(row: Dict[str, Any]) -> str:
    if row.get("venue") and row.get("year"):
        return f"{row['venue']} {row['year']}"
    return "unknown"


def build_prompt(row: Dict[str, Any], text: str, char_limit: int = TEXT_CHAR_LIMIT) -> str:
    body = clean_text(text)[:char_limit] or "(first-pages text unavailable)"
    return USER_TEMPLATE.format(
        title=clean_text(row.get("title") or "unknown"),
        venue_year=venue_year(row),
        abstract=clean_text(row.get("abstract") or "") or "(none)",
        char_limit=char_limit,
        text=body,
    )


def retry_prompt(base_prompt: str, errors: List[str], previous: str) -> str:
    return base_prompt + RETRY_TEMPLATE.format(
        errors="\n".join(f"- {e}" for e in errors), previous=previous[:3000])


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def hint_one(row: Dict[str, Any], hints_dir: Path, model: str, thinking: str, omp_cwd: Path,
             caller=None, text_fn=None) -> Dict[str, Any]:
    """Produce hints/<id>.json or hints/<id>.error.json for one catalog row."""
    caller = caller or call_omp
    text_fn = text_fn or pdf_text
    rid = row["id"]
    start = time.monotonic()
    text = text_fn(Path(row["pdf_path"]), 1, 2)
    base = build_prompt(row, text)
    prompt = base
    cost = 0.0
    attempts = 0
    errors: List[str] = []
    raw = ""
    kind = ""
    meta_extra: Dict[str, Any] = {}
    for attempt in (1, 2):
        attempts = attempt
        try:
            parsed = caller(prompt, model, thinking, omp_cwd)
        except OmpError as exc:
            cost += exc.cost
            kind = exc.kind
            errors = [exc.detail]
            break
        cost += parsed["cost"]
        raw = parsed["text"]
        meta_extra = {"served_model": parsed.get("model"), "provider": parsed.get("provider")}
        try:
            obj = extract_json_object(raw)
            errors = validate_hint(obj)
        except (ValueError, json.JSONDecodeError) as exc:
            obj = None
            errors = [f"output is not valid JSON: {exc}"]
        kind = "validation"
        if not errors:
            record = {
                "id": rid, "status": "ok", "prompt_version": prompt_version(), "model": model,
                "thinking": thinking, **meta_extra, "created_at": now_iso(),
                "seconds": round(time.monotonic() - start, 2), "cost_usd": round(cost, 6),
                "attempts": attempts, "text_chars": len(clean_text(text)), "hint": obj,
            }
            atomic_write(hints_dir / f"{rid}.json", json.dumps(record, ensure_ascii=False, indent=1) + "\n")
            return {"id": rid, "status": "ok", "seconds": record["seconds"], "cost_usd": record["cost_usd"],
                    "attempts": attempts, "error_kind": None, "error": None}
        prompt = retry_prompt(base, errors, raw)
    seconds = round(time.monotonic() - start, 2)
    record = {
        "id": rid, "status": "error", "error_kind": kind, "errors": errors, "prompt_version": prompt_version(),
        "model": model, "thinking": thinking, **meta_extra, "created_at": now_iso(), "seconds": seconds,
        "cost_usd": round(cost, 6), "attempts": attempts, "raw_output": raw[:RAW_KEEP_CHARS],
    }
    atomic_write(hints_dir / f"{rid}.error.json", json.dumps(record, ensure_ascii=False, indent=1) + "\n")
    return {"id": rid, "status": "error", "seconds": seconds, "cost_usd": round(cost, 6), "attempts": attempts,
            "error_kind": kind, "error": "; ".join(errors)[:500]}


INFRA_KINDS = {"timeout", "exit", "no_message", "stop_error", "rate_limit", "auth", "exception"}


def spent_so_far(log_path: Path) -> float:
    return sum(float(r.get("cost_usd") or 0.0) for r in read_jsonl(log_path))


def select_rows(rows: List[Dict[str, Any]], hints_dir: Path, ids: Optional[List[str]], limit: Optional[int]
                ) -> List[Dict[str, Any]]:
    pending = [r for r in rows if not (hints_dir / f"{r['id']}.json").exists()]
    if ids:
        wanted = set(ids)
        pending = [r for r in pending if r["id"] in wanted]
    if limit is not None:
        pending = pending[:limit]
    return pending


def cmd_hints(args: argparse.Namespace, caller=None) -> Dict[str, Any]:
    caller = caller or call_omp
    out = Path(args.out)
    rows = read_jsonl(out / "catalog.jsonl")
    if not rows:
        raise SystemExit(f"no catalog at {out / 'catalog.jsonl'}; run the catalog subcommand first")
    hints_dir = out / "hints"
    log_path = out / "build_log.jsonl"
    todo = select_rows(rows, hints_dir, args.ids, args.limit)
    spent = spent_so_far(log_path)
    summary: Dict[str, Any] = {"to_call": len(todo), "prompt_version": prompt_version(), "spent_before_usd": round(spent, 4)}
    if args.dry_run:
        summary["dry_run"] = True
        if todo:
            summary["first_id"] = todo[0]["id"]
            print(build_prompt(todo[0], pdf_text(Path(todo[0]["pdf_path"]), 1, 2)))
        print(json.dumps(summary, indent=1))
        return summary
    if spent >= args.cost_cap_usd:
        raise SystemExit(f"cost cap reached before start: spent ${spent:.4f} >= ${args.cost_cap_usd}")
    hints_dir.mkdir(parents=True, exist_ok=True)
    omp_cwd = Path(args.omp_cwd)
    omp_cwd.mkdir(parents=True, exist_ok=True)
    counts = {"ok": 0, "error": 0}
    kinds: Dict[str, int] = {}
    consecutive_infra = 0
    stop_reason = None
    queue = list(todo)
    started = time.monotonic()
    with cf.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool, open(log_path, "a", encoding="utf-8") as log:
        running: Dict[cf.Future, str] = {}
        while queue or running:
            while queue and stop_reason is None and len(running) < max(1, args.workers):
                row = queue.pop(0)
                fut = pool.submit(hint_one, row, hints_dir, args.model, args.thinking, omp_cwd, caller)
                running[fut] = row["id"]
            if not running:
                break
            done, _ = cf.wait(running, return_when=cf.FIRST_COMPLETED)
            for fut in done:
                rid = running.pop(fut)
                try:
                    res = fut.result()
                except Exception as exc:  # defensive: a worker bug must not lose the log line
                    res = {"id": rid, "status": "error", "seconds": None, "cost_usd": 0.0, "attempts": 0,
                           "error_kind": "exception", "error": repr(exc)[:500]}
                entry = {"ts": now_iso(), **res, "model": args.model, "thinking": args.thinking,
                         "prompt_version": prompt_version()}
                log.write(json.dumps(entry, ensure_ascii=False) + "\n")
                log.flush()
                spent += float(res.get("cost_usd") or 0.0)
                counts[res["status"]] = counts.get(res["status"], 0) + 1
                if res["status"] == "error":
                    kinds[res["error_kind"]] = kinds.get(res["error_kind"], 0) + 1
                if res["status"] == "error" and res["error_kind"] in INFRA_KINDS:
                    consecutive_infra += 1
                else:
                    consecutive_infra = 0
                n = counts["ok"] + counts["error"]
                if n % 25 == 0 or res["status"] == "error":
                    print(f"[{n}/{len(todo)}] ok={counts['ok']} error={counts['error']} spent=${spent:.3f} "
                          f"elapsed={time.monotonic() - started:.0f}s last={rid}:{res['status']}"
                          + (f" {res['error_kind']}: {str(res['error'])[:160]}" if res["status"] == "error" else ""),
                          flush=True)
                if stop_reason is None and spent >= args.cost_cap_usd:
                    stop_reason = f"cost cap ${args.cost_cap_usd} reached (spent ${spent:.4f})"
                if stop_reason is None and consecutive_infra >= args.max_consecutive_infra_errors:
                    stop_reason = f"{consecutive_infra} consecutive infrastructure errors (last {res['error_kind']}: {res['error']})"
    summary.update({"ok": counts.get("ok", 0), "error": counts.get("error", 0), "error_kinds": kinds,
                    "not_started": len(queue), "spent_total_usd": round(spent, 4),
                    "wall_s": round(time.monotonic() - started, 1), "stopped": stop_reason})
    print(json.dumps(summary, indent=1))
    return summary


# ---------------------------------------------------------------------------------------------
# Navigate

def load_hint_records(hints_dir: Path) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    ok: Dict[str, Dict[str, Any]] = {}
    err: Dict[str, Dict[str, Any]] = {}
    if not hints_dir.exists():
        return ok, err
    for path in sorted(hints_dir.glob("*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        if path.name.endswith(".error.json"):
            err[rec["id"]] = rec
        else:
            ok[rec["id"]] = rec
    # An ok hint takes precedence over a stale error file for the same id.
    err = {k: v for k, v in err.items() if k not in ok}
    return ok, err


def merged_rows(catalog: List[Dict[str, Any]], ok: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for c in catalog:
        rec = ok.get(c["id"])
        if rec is None:
            continue
        row = {"id": c["id"], "venue": c.get("venue"), "year": c.get("year"), "title": c.get("title"),
               "arxiv_id": c.get("arxiv_id"), "pdf_path": c.get("pdf_path")}
        row.update(rec["hint"])
        row.update({"prompt_version": rec.get("prompt_version"), "model": rec.get("model"),
                    "thinking": rec.get("thinking"), "confidence": rec["hint"].get("confidence")})
        rows.append(row)
    return rows


def md_escape(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).replace("|", "\\|").strip()


def paper_line(row: Dict[str, Any]) -> str:
    vy = f"{row['venue']} {row['year']}" if row.get("venue") else "loose"
    return f"{row['id']} — {md_escape(row.get('title'))} ({vy})"


def cmd_navigate(args: argparse.Namespace) -> Dict[str, Any]:
    out = Path(args.out)
    catalog = read_jsonl(out / "catalog.jsonl")
    if not catalog:
        raise SystemExit(f"no catalog at {out / 'catalog.jsonl'}")
    ok, err = load_hint_records(out / "hints")
    rows = merged_rows(catalog, ok)
    log = read_jsonl(out / "build_log.jsonl")
    total_cost = sum(float(r.get("cost_usd") or 0.0) for r in log)
    versions = sorted({r.get("prompt_version") for r in rows if r.get("prompt_version")})
    catalog_ids = {c["id"] for c in catalog}
    pending = sorted(catalog_ids - set(ok) - set(err))
    rel_counts = {k: sum(1 for r in rows if r.get("hmasd_relevance") == k) for k in (3, 2, 1, 0)}
    stats = {"catalog_rows": len(catalog), "hints_ok": len(rows), "hints_error": len(err), "pending": len(pending),
             "relevance_counts": rel_counts, "calls_logged": len(log), "total_cost_usd": round(total_cost, 4),
             "prompt_versions": versions}
    print(json.dumps(stats, indent=1))
    if args.dry_run:
        return stats

    write_jsonl(out / "hints.jsonl", rows)

    lines = [f"# My-lib LLM index — by topic\n\n",
             f"Generated {now_iso()} from {len(rows)} hints (model {args.model}, thinking {args.thinking}). "
             "Hints locate papers; they are not evidence.\n\n"]
    lines.append("| topic | papers |\n|---|---|\n")
    for topic in TOPICS:
        lines.append(f"| {topic} | {sum(1 for r in rows if topic in r.get('topics', []))} |\n")
    for topic in TOPICS:
        members = [r for r in rows if topic in r.get("topics", [])]
        lines.append(f"\n## {topic} ({len(members)})\n\n")
        members.sort(key=lambda r: (-int(r.get("hmasd_relevance", 0)), str(r["id"])))
        for r in members:
            lines.append(f"- {paper_line(r)} [rel {r.get('hmasd_relevance')}]\n")
    atomic_write(out / "INDEX_BY_TOPIC.md", "".join(lines))

    lines = [f"# My-lib LLM index — by HMASD relevance\n\n",
             "Relevance to hierarchical MARL skill coordination or UAV swarm cooperative/path planning, "
             "as judged by the index model from the title, abstract and first two pages. Hints locate papers; "
             "they are not evidence.\n\n",
             f"Counts: 3 = {rel_counts[3]}, 2 = {rel_counts[2]}, 1 = {rel_counts[1]}, 0 = {rel_counts[0]}.\n"]
    for level in (3, 2):
        members = sorted((r for r in rows if r.get("hmasd_relevance") == level), key=lambda r: str(r["id"]))
        lines.append(f"\n## Relevance {level} ({len(members)})\n\n")
        for r in members:
            lines.append(f"- {paper_line(r)}: {md_escape(r.get('one_line_hint'))} "
                         f"_(why: {md_escape(r.get('hmasd_relevance_reason'))})_\n")
    atomic_write(out / "INDEX_BY_RELEVANCE.md", "".join(lines))

    err_kinds: Dict[str, int] = {}
    for rec in err.values():
        err_kinds[rec.get("error_kind") or "?"] = err_kinds.get(rec.get("error_kind") or "?", 0) + 1
    conf_counts: Dict[str, int] = {}
    for r in rows:
        conf_counts[str(r.get('confidence'))] = conf_counts.get(str(r.get('confidence')), 0) + 1
    stale_errors = len(list((out / "hints").glob("*.error.json"))) - len(err)
    abstract_short = sum(1 for c in catalog if len(c.get("abstract") or "") < 100)
    readme = f"""# My-lib LLM index

A lightweight search aid over the My-lib paper corpus
(`{Path(args.corpus_root)}`): one deterministic catalog row per PDF and one short LLM-written
index hint per paper. **Hints locate papers; they are not evidence. A miss says nothing beyond this
corpus.** Read the PDF before relying on anything a hint says.

- Build date: {now_iso()}
- Builder: `tools/reference_libraries/build_mylib_llm_index.py` in the HMASD repository (`{REPO_ROOT}`)
- Model: `{args.model}`, thinking `{args.thinking}`, via headless `omp -p --mode json` (per-call timeout {CALL_TIMEOUT_S} s)
- Prompt version (sha256 prefix of the system + user + retry templates and vocabularies): current `{prompt_version()}`; present in hints: {', '.join(versions) or 'none'}
- Input per paper: title, venue/year, arXiv abstract, `pdftotext -f 1 -l 2` text truncated to {TEXT_CHAR_LIMIT} characters

## Counts

- PDFs / catalog rows: {len(catalog)}
- Hints ok: {len(rows)}; hints failed: {len(err)} ({', '.join(f'{k}: {v}' for k, v in sorted(err_kinds.items())) or 'none'}); not yet attempted: {len(pending)}
- HMASD relevance: 3 = {rel_counts[3]}, 2 = {rel_counts[2]}, 1 = {rel_counts[1]}, 0 = {rel_counts[0]}
- Logged paper attempts (`build_log.jsonl` rows; a retry after a schema failure stays in one row): {len(log)}; total cost ${total_cost:.4f}

Failed ids: {', '.join(sorted(err)) or 'none'}

Superseded error files (a later attempt succeeded): {stale_errors}

## Files

- `catalog.jsonl` — one row per PDF (`id`, `official_id`, `venue`, `year`, `title`, `arxiv_id`, `authors`, `published`,
  `abstract`, `official_url`, `title_screen_hits`, `pdf_path`, `pdf_bytes`, `pages`).
- `titles.tsv` — `id venue year title arxiv_id`.
- `hints/<id>.json` — per-paper hint with provenance; `hints/<id>.error.json` — failed attempt. A later
  successful `hints/<id>.json` takes precedence; stale error files are left in place.
- `hints.jsonl` — merged ok hints joined with catalog fields.
- `INDEX_BY_TOPIC.md`, `INDEX_BY_RELEVANCE.md` — navigation pages.
- `build_log.jsonl` — one row per paper attempt (id, seconds, cost, ok/error).

## Data caveats

- The arXiv `summary` in the acquisition match file is truncated for most records ({abstract_short} of
  {len(catalog)} catalog abstracts are shorter than 100 characters); hints rely mainly on the first two pages.
- Relevance scores and topics are one model's reading of the first pages; they miss papers whose
  relevance appears later in the text. `hmasd_relevance_reason` often names the HMASD themes when
  explaining non-relevance, so `search_mylib.py` does not search that field.
- Model-reported confidence: {', '.join(f'{k} {v}' for k, v in sorted(conf_counts.items())) or 'none'}; a
  uniform value carries no ranking information.

## Search and rebuild

```bash
python3 {REPO_ROOT}/tools/reference_libraries/search_mylib.py UAV multi-agent
python3 {REPO_ROOT}/tools/reference_libraries/build_mylib_llm_index.py all   # resumable; only missing hints are called
python3 {REPO_ROOT}/tools/reference_libraries/build_mylib_llm_index.py navigate
```
"""
    atomic_write(out / "README.md", readme)
    return stats


# ---------------------------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("catalog", "hints", "navigate", "all"))
    parser.add_argument("--corpus-root", default=str(DEFAULT_CORPUS_ROOT))
    parser.add_argument("--matches-json", default=str(DEFAULT_MATCHES_JSON))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--omp-cwd", default=str(DEFAULT_OMP_CWD), help="working directory for omp (not ~)")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--limit", type=int, default=None, help="at most this many pending papers")
    parser.add_argument("--ids", action="append", default=None, help="only these catalog ids (repeatable)")
    parser.add_argument("--cost-cap-usd", type=float, default=25.0,
                        help="stop submitting when the cumulative cost in build_log.jsonl reaches this")
    parser.add_argument("--max-consecutive-infra-errors", type=int, default=5)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--thinking", default=DEFAULT_THINKING)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command in ("catalog", "all"):
        cmd_catalog(args)
    if args.command in ("hints", "all"):
        summary = cmd_hints(args)
        if summary.get("stopped"):
            print(f"hints stopped: {summary['stopped']}", file=sys.stderr)
    if args.command in ("navigate", "all"):
        cmd_navigate(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
