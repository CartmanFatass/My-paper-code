"""One-shot CLI for the zero-runtime ORBIT-A2 registered audit."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.orbit_shadow_read.verified_owner_binding_reachability import (
    ASSIGNMENT_ID,
    CANDIDATE,
    SOURCE_PATHS,
    run_verified_owner_binding_audit,
)


CLAIM_NAME = "registered_claim.json"
RESULT_NAME = "raw_result.json"


def _head_revision() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _require_clean_bound_sources() -> None:
    tracked = tuple(
        sorted(
            subprocess.run(
                ["git", "ls-files", "--", *SOURCE_PATHS],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.splitlines()
        )
    )
    expected = tuple(sorted(SOURCE_PATHS))
    if tracked != expected:
        missing = tuple(sorted(set(expected) - set(tracked)))
        raise ValueError(f"registered audit source is untracked or absent: {missing}")
    dirty = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all", "--", *SOURCE_PATHS],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    if dirty:
        raise ValueError(f"registered audit sources differ from HEAD: {dirty}")


def _exclusive_write(path: Path, payload: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _run(args: argparse.Namespace) -> int:
    actual_revision = _head_revision()
    if args.source_commit != actual_revision:
        raise ValueError(
            f"source commit {args.source_commit!r} does not match checkout HEAD {actual_revision}"
        )
    _require_clean_bound_sources()
    run_root = args.run_root.resolve()
    run_root.mkdir(parents=True, exist_ok=True)
    claim_path = run_root / CLAIM_NAME
    result_path = run_root / RESULT_NAME
    if result_path.exists():
        raise FileExistsError(f"registered result already exists: {result_path}")
    claim = {
        "artifact_kind": "ORBIT_A2_REGISTERED_AUDIT_CLAIM",
        "assignment_id": ASSIGNMENT_ID,
        "candidate": CANDIDATE,
        "source_commit": actual_revision,
        "result_name": RESULT_NAME,
        "route_cell_call_cap": 15,
        "environment_transition_cap": 0,
    }
    _exclusive_write(
        claim_path,
        json.dumps(
            claim, ensure_ascii=True, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        + b"\n",
    )
    # The claim now exists.  Any later failure is terminal; this CLI never retries.
    result = run_verified_owner_binding_audit()
    _exclusive_write(result_path, result.to_bytes() + b"\n")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Execute the single deterministic ORBIT-A2 verified-owner-binding audit; "
            "creates a terminal write-once claim before any route-cell call"
        )
    )
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.set_defaults(handler=_run)
    return parser


def main() -> int:
    args = _parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
