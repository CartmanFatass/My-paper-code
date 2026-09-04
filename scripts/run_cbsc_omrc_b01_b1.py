"""Canonical fail-closed CLI for CBSC-OMRC-B1 engineering readiness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.artifact import (
    canonical_json_bytes,
    ensure_confined,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1 import (
    B1OrchestrationError,
    CONFINED_ROOT,
    readiness_document,
    run_assess_preflight,
    run_b1_resume,
    run_b1_start,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_contract import (
    B1Plan,
)


def _write_create_only(path: Path, value: Any) -> Path:
    destination = ensure_confined(path, CONFINED_ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        stream.write(canonical_json_bytes(value) + b"\n")
        stream.flush()
    return destination


def validation_document() -> dict[str, Any]:
    readiness = readiness_document()
    return {
        "status": readiness["status"],
        "configuration": B1Plan().as_dict(),
        "allowed_modes": ["validate", "readiness", "assess-run", "start", "resume"],
        "engine_contract": "CANONICAL_FIXED_FACTORY_AND_WORKER_ONLY",
        "formal_analysis_bound": readiness["formal_analysis_bound"],
        "start_authorized": readiness["start_authorized"],
        "resume_authorized": readiness["resume_authorized"],
        "decision": "DECISION_PENDING",
        "scientific_branch": None,
        "performance_disposition": "PILOT_ONLY",
        "production_assembly_ready": readiness["production_assembly_ready"],
        "readiness_disposition": readiness["readiness_disposition"],
        "blockers": readiness["blockers"],
        "blocker": readiness["blocker"],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    validate = modes.add_parser("validate")
    validate.add_argument("--output", type=Path)
    readiness = modes.add_parser("readiness")
    readiness.add_argument("--implementation-commit")
    readiness.add_argument("--b0-root", type=Path)
    readiness.add_argument("--output", type=Path)
    assess = modes.add_parser("assess-run")
    assess.add_argument("--output", type=Path, required=True)
    start = modes.add_parser("start")
    start.add_argument("--output", type=Path, required=True)
    start.add_argument("--implementation-commit", required=True)
    start.add_argument("--b0-root", type=Path, required=True)
    resume = modes.add_parser("resume")
    resume.add_argument("--output", type=Path, required=True)
    resume.add_argument("--implementation-commit", required=True)
    resume.add_argument("--b0-root", type=Path, required=True)
    resume.add_argument("--incident-root", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.mode == "validate":
            document = validation_document()
            if args.output is not None:
                _write_create_only(args.output, document)
            print(json.dumps(document, indent=2, sort_keys=True))
            return 0
        if args.mode == "readiness":
            document = readiness_document(args.implementation_commit, args.b0_root)
            if args.output is not None:
                _write_create_only(args.output, document)
            print(json.dumps(document, indent=2, sort_keys=True))
            return 0 if document["start_authorized"] else 4
        if args.mode == "assess-run":
            document = run_assess_preflight(args.output)
            print(json.dumps(document, indent=2, sort_keys=True))
            return 0 if document.get("memory_safe") is True else 6
        if args.mode == "start":
            published = run_b1_start(
                final_path=args.output, implementation_commit=args.implementation_commit,
                b0_root=args.b0_root,
            )
        else:
            published = run_b1_resume(
                final_path=args.output, implementation_commit=args.implementation_commit,
                b0_root=args.b0_root, incident_root=args.incident_root,
            )
        print(json.dumps({
            "published": str(published), "decision": "DECISION_PENDING",
            "scientific_branch": None,
        }, indent=2))
        return 0
    except (B1OrchestrationError, FileExistsError, ValueError, OSError) as exc:
        print(f"CBSC OMRC B1 refused: {exc}", file=sys.stderr)
        return 6


if __name__ == "__main__":
    raise SystemExit(main())
