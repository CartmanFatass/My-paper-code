#!/usr/bin/env python3
"""Normalize recorded paper-lookup fixtures or explicitly fetch a named endpoint.

Adapted from K-Dense Inc.'s MIT-licensed paper-lookup scripts at
skills/paper-lookup/scripts/{arxiv_atom,openalex_abstract,jats_to_text,paginate,_common}.py,
commit f6fcafeb1cc8c82eca0160a18bc41c38427b8e0f.

Copyright (c) 2025 K-Dense Inc.
MIT License: permission is hereby granted, free of charge, to use, copy,
modify, merge, publish, distribute, sublicense, and/or sell copies, subject
to inclusion of this copyright and permission notice in copies or substantial
portions. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

try:
    from .fetch import fetch_named_endpoint, parse_parameter_json
    from .normalizers import (
        PaperLookupInputError,
        load_json_text,
        normalize_arxiv_atom,
        normalize_jats,
        normalize_openalex,
        reconcile_pagination,
    )
except ImportError:  # Direct CLI execution has no package context.
    from fetch import fetch_named_endpoint, parse_parameter_json
    from normalizers import (
        PaperLookupInputError,
        load_json_text,
        normalize_arxiv_atom,
        normalize_jats,
        normalize_openalex,
        reconcile_pagination,
    )


def _read_source(source: str) -> str:
    if source == "-":
        text = sys.stdin.read()
    else:
        path = Path(source)
        if not path.is_file():
            raise PaperLookupInputError(f"source must be a local file or stdin ('-'), not {source!r}")
        text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise PaperLookupInputError("source is empty")
    return text


def _emit(payload: dict[str, Any], stream: Any = sys.stdout) -> None:
    json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
    stream.write("\n")


def _success(result: dict[str, Any], *, network_used: bool) -> dict[str, Any]:
    return {
        "network_used": network_used,
        "result": result,
        "schema_version": 1,
        "scientific_effect": "none",
        "tool": "paper_lookup",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    for command in ("arxiv", "openalex", "jats", "paginate"):
        item = subcommands.add_parser(command, help=f"normalize a recorded {command} fixture")
        item.add_argument("source", help="local fixture path or - for stdin; never a URL")
    fetch = subcommands.add_parser("fetch", help="explicitly fetch one supported public endpoint")
    fetch.add_argument("--allow-network", action="store_true", help="required explicit opt-in to network I/O")
    fetch.add_argument("--endpoint", required=True, choices=("arxiv", "openalex"), help="named public endpoint")
    fetch.add_argument("--params-json", required=True, help="JSON object of non-secret string request parameters")
    fetch.add_argument("--timeout-seconds", type=int, default=10, help="bounded timeout from 1 through 30 seconds")
    fetch.add_argument("--access-date", required=True, help="UTC access date in ISO-8601 YYYY-MM-DD form")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "fetch":
            try:
                date.fromisoformat(args.access_date)
            except ValueError as error:
                raise PaperLookupInputError("access_date must be an ISO-8601 YYYY-MM-DD date") from error
            result = fetch_named_endpoint(
                args.endpoint,
                parse_parameter_json(args.params_json),
                allow_network=args.allow_network,
                timeout_seconds=args.timeout_seconds,
            )
            result["access_date"] = args.access_date
            _emit(_success(result, network_used=True))
            return 0

        source = _read_source(args.source)
        if args.command == "arxiv":
            result = normalize_arxiv_atom(source)
        elif args.command == "openalex":
            result = normalize_openalex(load_json_text(source))
        elif args.command == "jats":
            result = normalize_jats(source)
        else:
            result = reconcile_pagination(load_json_text(source))
        _emit(_success(result, network_used=False))
        return 0
    except PaperLookupInputError as error:
        _emit(
            {
                "error": {"code": "INVALID_INPUT", "message": str(error)},
                "network_used": False,
                "schema_version": 1,
                "scientific_effect": "none",
                "tool": "paper_lookup",
            },
            sys.stderr,
        )
        return 2
    except OSError as error:
        _emit(
            {
                "error": {"code": "FETCH_OR_IO_ERROR", "message": str(error)},
                "network_used": args.command == "fetch" and args.allow_network,
                "schema_version": 1,
                "scientific_effect": "none",
                "tool": "paper_lookup",
            },
            sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
