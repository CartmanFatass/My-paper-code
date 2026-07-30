"""Read-only, JSON-first access probe for the InstSci MyLib corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable


DEFAULT_MYLIB_ROOT = Path(r"C:\Projects\Inst-sci\papers\MyLib")
REGISTERED_LOCAL_RESEARCH_ROOT = Path(__file__).resolve().parents[4] / "local_research"


class ProbeError(RuntimeError):
    """A fail-closed MyLib access or output-boundary error."""


def _canonical(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _inside(path: Path, root: Path) -> bool:
    try:
        return os.path.commonpath(
            (os.path.normcase(str(path)), os.path.normcase(str(root)))
        ) == os.path.normcase(str(root))
    except ValueError:
        return False


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProbeError(f"required file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProbeError(f"invalid JSON: {path}: {exc}") from exc


def _integrity(root: Path) -> dict[str, Any]:
    value = _read_json(root / "metadata" / "integrity.json")
    if not isinstance(value, dict):
        raise ProbeError("integrity.json must contain one object")
    if value.get("content_contract") != "pdf+json+metadata+llm-index":
        raise ProbeError("MyLib content_contract is not the registered JSON-only contract")
    for key in ("actual", "expected", "missing_json_ids"):
        if key not in value:
            raise ProbeError(f"integrity.json is missing {key}")
    metadata_v2 = value.get("metadata_v2")
    if not isinstance(metadata_v2, dict) or metadata_v2.get("status") != "validated":
        raise ProbeError("MyLib metadata_v2 is not validated")
    for key in ("catalog", "full_jsonl", "schema", "quality_report", "records"):
        if key not in metadata_v2:
            raise ProbeError(f"integrity.json metadata_v2 is missing {key}")
    return value


def _read_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise ProbeError(f"{label} is missing: {path}") from exc
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ProbeError(f"invalid {label} row {line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise ProbeError(f"{label} row {line_number} is not an object")
        records.append(value)
    return records


def _resolve_registered_path(root: Path, raw: Any, fallback: Path) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        return _canonical(fallback)
    relative = Path(raw.replace("/", os.sep).replace("\\", os.sep))
    if relative.is_absolute():
        candidate = _canonical(relative)
    else:
        root_markers = [
            index
            for index, part in enumerate(relative.parts)
            if part.casefold() == root.name.casefold()
        ]
        if root_markers:
            suffix = relative.parts[root_markers[-1] + 1 :]
            candidate = _canonical(root.joinpath(*suffix))
        else:
            candidate = _canonical(root / relative)
    if not _inside(candidate, root):
        raise ProbeError(f"registered path escapes MyLib: {candidate}")
    return candidate


def _metadata_paths(root: Path, integrity: dict[str, Any]) -> dict[str, Path]:
    metadata_v2 = integrity["metadata_v2"]
    paths = {
        key: _resolve_registered_path(root, metadata_v2[key], root / "missing")
        for key in ("catalog", "full_jsonl", "schema", "quality_report")
    }
    for key, path in paths.items():
        if not path.is_file():
            raise ProbeError(f"registered metadata_v2 {key} is missing: {path}")
    return paths


def _catalog(root: Path, integrity: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    registered = integrity or _integrity(root)
    path = _metadata_paths(root, registered)["catalog"]
    records = _read_jsonl(path, "metadata_v2 catalog")
    seen: set[str] = set()
    for line_number, value in enumerate(records, 1):
        if not value.get("id") or not value.get("title"):
            raise ProbeError(f"metadata_v2 catalog row {line_number} lacks id or title")
        paper_id = str(value["id"])
        if paper_id in seen:
            raise ProbeError(f"metadata_v2 catalog id is duplicated: {paper_id}")
        seen.add(paper_id)
        if "relative_md_path" in value or "md_path" in value:
            raise ProbeError("metadata_v2 catalog exposes the retired Markdown layer")
    expected = registered["metadata_v2"]["records"]
    if len(records) != expected:
        raise ProbeError(
            f"metadata_v2 catalog count mismatch: expected {expected}, got {len(records)}"
        )
    return records


def _metadata_records(
    root: Path, integrity: dict[str, Any] | None = None
) -> tuple[list[dict[str, Any]], Path]:
    registered = integrity or _integrity(root)
    path = _metadata_paths(root, registered)["full_jsonl"]
    records = _read_jsonl(path, "metadata_v2 full record")
    seen: set[str] = set()
    for line_number, value in enumerate(records, 1):
        paper_id = value.get("id")
        if not isinstance(paper_id, str) or not paper_id:
            raise ProbeError(f"metadata_v2 full row {line_number} lacks id")
        if paper_id in seen:
            raise ProbeError(f"metadata_v2 full record id is duplicated: {paper_id}")
        seen.add(paper_id)
        if not isinstance(value.get("quality"), dict):
            raise ProbeError(f"metadata_v2 full row {line_number} lacks quality")
        provenance = value.get("provenance")
        if not isinstance(provenance, dict) or not isinstance(
            provenance.get("field_evidence"), dict
        ):
            raise ProbeError(
                f"metadata_v2 full row {line_number} lacks provenance.field_evidence"
            )
    expected = registered["metadata_v2"]["records"]
    if len(records) != expected:
        raise ProbeError(
            f"metadata_v2 full record count mismatch: expected {expected}, got {len(records)}"
        )
    return records, path


def _record(root: Path, paper_id: str) -> dict[str, Any]:
    matches = [item for item in _catalog(root) if item.get("id") == paper_id]
    if len(matches) != 1:
        raise ProbeError(f"paper id must resolve exactly once: {paper_id}")
    return matches[0]


def _metadata_record(
    root: Path, paper_id: str, integrity: dict[str, Any] | None = None
) -> tuple[dict[str, Any], Path]:
    records, path = _metadata_records(root, integrity)
    matches = [item for item in records if item.get("id") == paper_id]
    if len(matches) != 1:
        raise ProbeError(f"metadata_v2 paper id must resolve exactly once: {paper_id}")
    return matches[0], path


def _paths(root: Path, record: dict[str, Any]) -> tuple[Path, Path, Path]:
    paper_id = str(record["id"])
    pdf = _resolve_registered_path(
        root,
        record.get("pdf_path", record.get("relative_pdf_path")),
        root / "pdf" / f"{paper_id}.pdf",
    )
    structured = _resolve_registered_path(
        root,
        record.get("json_path", record.get("relative_json_path")),
        root / "json" / f"{paper_id}.json",
    )
    assets = _canonical(root / "assets" / paper_id)
    return pdf, structured, assets


def _text_fields(value: Any, key: str = "") -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        for child_key, child in value.items():
            if isinstance(child, str) and child_key.casefold() in {
                "text",
                "content",
                "value",
            }:
                cleaned = " ".join(child.split())
                if cleaned:
                    yield {"field": child_key, "text": cleaned}
            else:
                yield from _text_fields(child, child_key)
    elif isinstance(value, list):
        for child in value:
            yield from _text_fields(child, key)


def _validate_json(path: Path) -> dict[str, Any]:
    document = _read_json(path)
    fields = list(_text_fields(document))
    if not fields:
        raise ProbeError(f"structured JSON has no core text/content/value fields: {path}")
    return {
        "exists": True,
        "path": str(path),
        "core_text_field_count": len(fields),
        "sample": fields[0]["text"][:240],
    }


def _validate_pdf(path: Path) -> dict[str, Any]:
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return {"exists": False, "path": str(path), "valid": False, "reason": "missing_pdf"}
    reason = "ok"
    valid = True
    if not data.startswith(b"%PDF-"):
        valid, reason = False, "missing_pdf_header"
    elif b"%%EOF" not in data[-2048:]:
        valid, reason = False, "missing_pdf_eof"
    return {
        "exists": True,
        "path": str(path),
        "valid": valid,
        "reason": reason,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _status(root: Path) -> dict[str, Any]:
    integrity = _integrity(root)
    paths = _metadata_paths(root, integrity)
    _read_json(paths["schema"])
    quality_report = _read_json(paths["quality_report"])
    if not isinstance(quality_report, dict):
        raise ProbeError("metadata_v2 quality report must contain one object")
    return {
        "content_contract": integrity["content_contract"],
        "actual": integrity["actual"],
        "expected": integrity["expected"],
        "missing_json_ids": integrity["missing_json_ids"],
        "duplicate_ids": integrity.get("duplicate_ids", []),
        "integrity_path": str(root / "metadata" / "integrity.json"),
        "metadata_v2": {
            "status": integrity["metadata_v2"]["status"],
            "records": integrity["metadata_v2"]["records"],
            "quality_grades": integrity["metadata_v2"].get("quality_grades", {}),
            "catalog_path": str(paths["catalog"]),
            "full_jsonl_path": str(paths["full_jsonl"]),
            "schema_path": str(paths["schema"]),
            "quality_report_path": str(paths["quality_report"]),
        },
    }


def _searchable_strings(value: Any, key: str = "") -> Iterable[str]:
    if isinstance(value, dict):
        for child_key, child in value.items():
            yield from _searchable_strings(child, child_key.casefold())
    elif isinstance(value, list):
        for child in value:
            yield from _searchable_strings(child, key)
    elif isinstance(value, (str, int, float)):
        if key.endswith("_path") or key.endswith("_sha256") or key in {
            "pdf_sha256",
            "source_url",
            "official_url",
            "pdf_url",
        }:
            return
        yield str(value)


def _search(root: Path, query: str, limit: int) -> dict[str, Any]:
    integrity = _integrity(root)
    full_records, metadata_path = _metadata_records(root, integrity)
    full_by_id = {str(item["id"]): item for item in full_records}
    needle = query.casefold()
    results: list[dict[str, Any]] = []
    for record in _catalog(root, integrity):
        haystack = " ".join(_searchable_strings(record)).casefold()
        if needle not in haystack:
            continue
        paper_id = str(record["id"])
        full = full_by_id.get(paper_id)
        if full is None:
            raise ProbeError(f"catalog id lacks a metadata_v2 full record: {paper_id}")
        quality = full["quality"]
        field_evidence = full["provenance"]["field_evidence"]
        pdf, structured, _ = _paths(root, record)
        results.append(
            {
                "id": paper_id,
                "title": record["title"],
                "quality_grade": quality.get("grade"),
                "quality_warnings": quality.get("warnings", []),
                "semantic_status": quality.get("semantic_status"),
                "provenance_field_evidence": field_evidence,
                "metadata_path": str(metadata_path),
                "json_path": str(structured),
                "pdf_path": str(pdf),
            }
        )
        if len(results) >= limit:
            break
    return {
        "evidence_authority": "discovery_only",
        "semantic_scope": "title_or_abstract_only",
        "empty_or_unspecified_are_unknown": True,
        "query": query,
        "results": results,
    }


def _locate(root: Path, paper_id: str) -> dict[str, Any]:
    integrity = _integrity(root)
    record = _record(root, paper_id)
    full, metadata_path = _metadata_record(root, paper_id, integrity)
    pdf, structured, assets = _paths(root, record)
    json_missing = paper_id in integrity["missing_json_ids"] or not structured.is_file()
    field_evidence = full["provenance"]["field_evidence"]
    research_evidence = field_evidence.get("research", {})
    abstract_evidence = field_evidence.get("abstract", {})
    evidence_url = None
    if isinstance(research_evidence, dict):
        evidence_url = research_evidence.get("evidence_url")
    if not json_missing and not evidence_url and isinstance(abstract_evidence, dict):
        evidence_url = abstract_evidence.get("url")
    if json_missing:
        caveats = (
            research_evidence.get("caveats", [])
            if isinstance(research_evidence, dict)
            else []
        )
        semantic_status = full["quality"].get("semantic_status")
        if not isinstance(caveats, list) or "abstract_only" not in caveats:
            raise ProbeError(
                f"metadata_v2 missing-JSON record lacks explicit abstract_only provenance: {paper_id}"
            )
        if not isinstance(evidence_url, str) or not evidence_url.strip():
            raise ProbeError(
                f"metadata_v2 missing-JSON record lacks a nonempty evidence_url: {paper_id}"
            )
        if semantic_status != "luna_official_abstract_grounded":
            raise ProbeError(
                f"metadata_v2 missing-JSON record has an unexpected semantic status: {paper_id}"
            )
    return {
        "paper_id": paper_id,
        "title": record["title"],
        "json_missing": json_missing,
        "content_entry": "pdf" if json_missing else "json",
        "detail_verification_entry": "pdf" if json_missing else "json",
        "abstract_only": json_missing,
        "evidence_url": evidence_url,
        "metadata": {"path": str(metadata_path), "exists": metadata_path.is_file()},
        "quality": full["quality"],
        "provenance_field_evidence": field_evidence,
        "semantic_scope": "title_or_abstract_only",
        "empty_or_unspecified_are_unknown": True,
        "json": {"path": str(structured), "exists": structured.is_file()},
        "pdf": {"path": str(pdf), "exists": pdf.is_file()},
        "assets": {"path": str(assets), "exists": assets.is_dir()},
        "legacy_markdown_allowed": False,
    }


def _smoke(root: Path) -> dict[str, Any]:
    status = _status(root)
    integrity = _integrity(root)
    full_records, _ = _metadata_records(root, integrity)
    full_by_id = {str(item["id"]): item for item in full_records}
    for record in _catalog(root, integrity):
        pdf, structured, _ = _paths(root, record)
        if not structured.is_file() or not pdf.is_file():
            continue
        json_result = _validate_json(structured)
        pdf_result = _validate_pdf(pdf)
        if not pdf_result["valid"]:
            continue
        full = full_by_id.get(str(record["id"]))
        if full is None:
            raise ProbeError(f"catalog id lacks a metadata_v2 full record: {record['id']}")
        return {
            "status": "MYLIB_READ_ONLY_SMOKE_OK",
            "content_contract": status["content_contract"],
            "paper_id": record["id"],
            "json_valid": True,
            "core_text_field_count": json_result["core_text_field_count"],
            "json_path": str(structured),
            "json_access_layer": True,
            "pdf_valid": True,
            "pdf_path": str(pdf),
            "metadata_v2_validated": status["metadata_v2"]["status"] == "validated",
            "quality_grade": full["quality"].get("grade"),
            "provenance_checked": bool(full["provenance"]["field_evidence"]),
            "legacy_markdown_allowed": False,
        }
    raise ProbeError("no catalog record has both valid structured JSON and valid PDF")


def _write_output(payload: dict[str, Any], output: str | None, local_root: Path) -> None:
    if output is None:
        return
    target = _canonical(Path(output))
    if not _inside(target, local_root):
        raise ProbeError(f"output must remain inside local_research: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mylib-root",
        default=os.environ.get("MYLIB_ROOT", str(DEFAULT_MYLIB_ROOT)),
    )
    parser.add_argument("--local-research-root", required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("status", "smoke"):
        command = subparsers.add_parser(name)
        command.add_argument("--output")
    search = subparsers.add_parser("search")
    search.add_argument("--query", required=True)
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--output")
    locate = subparsers.add_parser("locate")
    locate.add_argument("--paper-id", required=True)
    locate.add_argument("--output")
    validate = subparsers.add_parser("validate-pdf")
    validate.add_argument("--paper-id", required=True)
    validate.add_argument("--output")
    return parser


def main() -> int:
    args = _parser().parse_args()
    root = _canonical(Path(args.mylib_root))
    local_root = _canonical(Path(args.local_research_root))
    try:
        if not root.is_dir():
            raise ProbeError(f"MyLib root is missing: {root}")
        if not local_root.is_dir():
            raise ProbeError(f"local_research root is missing: {local_root}")
        registered_local_root = _canonical(REGISTERED_LOCAL_RESEARCH_ROOT)
        if local_root != registered_local_root:
            raise ProbeError(
                "local_research root must be the registered checkout directory: "
                f"{registered_local_root}"
            )
        if args.command == "status":
            result = _status(root)
        elif args.command == "search":
            if args.limit < 1:
                raise ProbeError("search limit must be positive")
            result = _search(root, args.query, args.limit)
        elif args.command == "locate":
            result = _locate(root, args.paper_id)
        elif args.command == "validate-pdf":
            record = _record(root, args.paper_id)
            pdf, _, _ = _paths(root, record)
            result = _validate_pdf(pdf)
            if not result["valid"]:
                print(json.dumps(result, ensure_ascii=False, sort_keys=True))
                return 2
        else:
            result = _smoke(root)
        _write_output(result, args.output, local_root)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (ProbeError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
