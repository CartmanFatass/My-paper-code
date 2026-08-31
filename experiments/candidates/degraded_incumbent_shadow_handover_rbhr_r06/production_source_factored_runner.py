"""Guarded direct runner: no scientific activity until all frozen gaps close."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import NoReturn, Sequence

from .production_source_factored_contract import (
    PRODUCTION_REQUEST_SCHEMA, RUNNER_MASTER_POLICY, SourceFactoredNotReady,
    canonical_json_bytes, production_readiness_gap_inventory,
)


def _request_keys(node: object, path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], str]]:
    result: list[tuple[tuple[str, ...], str]] = []
    if isinstance(node, dict):
        for raw_key, child in node.items():
            key = str(raw_key).lower()
            result.append((path, key))
            result.extend(_request_keys(child, (*path, key)))
    elif isinstance(node, list):
        for child in node:
            result.extend(_request_keys(child, path))
    return result


def _validate_request_header(value: object) -> None:
    if not isinstance(value, dict):
        raise ValueError("source-factored request must be a top-level object")
    if value.get("schema") != PRODUCTION_REQUEST_SCHEMA:
        raise ValueError("source-factored request schema differs")
    if value.get("master_policy") != RUNNER_MASTER_POLICY:
        raise ValueError("source-factored request master_policy differs")
    if value.get("caller_master_allowed") is not False:
        raise ValueError("source-factored request caller_master_allowed differs")
    allowed_top_level_policy_keys = {"master_policy", "caller_master_allowed"}
    forbidden_tokens = ("master", "seed", "rng_override")
    if any(
        not (not path and key in allowed_top_level_policy_keys) and
        any(token in key for token in forbidden_tokens)
        for path, key in _request_keys(value)
    ):
        raise ValueError("caller master/seed is forbidden")


def refuse_run(*, repository_root: Path, request: Path, run_root: Path) -> NoReturn:
    repository = Path(repository_root).resolve(); request_path = Path(request).resolve()
    target = Path(run_root).resolve()
    if not (repository / "AGENTS.md").is_file():
        raise ValueError("repository root differs")
    if target.exists():
        raise ValueError("source-factored run root must be fresh")
    if not request_path.is_file():
        raise ValueError("source-factored request is absent")
    try:
        value = json.loads(request_path.read_text(encoding="ascii"))
    except OSError as error:
        raise ValueError("source-factored request became unavailable") from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("source-factored request JSON differs") from error
    _validate_request_header(value)
    # Deliberately do not create the run root, master, model, coordinate, or
    # checkpoint.  Request admission cannot succeed while readiness is false.
    gaps = production_readiness_gap_inventory()
    raise SourceFactoredNotReady(
        "source-factored production is NOT READY: " + ",".join(gaps["gaps"])
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--run-root", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        run_root_preexisting: bool | None = args.run_root.exists()
    except OSError:
        run_root_preexisting = None
    try:
        refuse_run(repository_root=args.repository_root, request=args.request, run_root=args.run_root)
    except (SourceFactoredNotReady, ValueError, OSError) as error:
        try:
            run_root_present_at_refusal: bool | None = args.run_root.exists()
        except OSError:
            run_root_present_at_refusal = None
        receipt = {
            "schema": "DISH_BLOCK_CERTIFICATE_PREVALENCE_R02_RUN_REFUSAL_V2",
            "status": "NOT_READY", "exit_code": 2, "message": str(error),
            "reason": ("READINESS_GAPS" if isinstance(error, SourceFactoredNotReady)
                       else "INVALID_OR_UNAVAILABLE_REQUEST"),
            "run_root_preexisting": run_root_preexisting,
            "run_root_present_at_refusal": run_root_present_at_refusal,
            "run_root_created_by_runner": False, "master_created": False,
            "checkpoint_created": False, "result_created": False,
            "gap_inventory": production_readiness_gap_inventory(),
        }
        print(canonical_json_bytes(receipt).decode("ascii"), end="")
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
