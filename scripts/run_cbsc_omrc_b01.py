"""B0-only validation, readiness, assessment, and execution CLI for OMRC-B01."""

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
    B0_RUN_NAME,
    canonical_json_bytes,
    ensure_confined,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b0 import (
    B0ContractError,
    frozen_configuration,
    run_assess_preflight,
    run_b0,
    verify_source_conformance,
)


CONFINED_ROOT = (
    REPO_ROOT / "temp" / "directions" / "capability_bound_semantic_currentness"
).resolve(strict=False)
DEFAULT_PREFLIGHT = (REPO_ROOT / "scripts" / "hmasd_resource_preflight.py").resolve()


def _write_create_only(path: Path, value: Any) -> Path:
    destination = ensure_confined(path, CONFINED_ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        stream.write(canonical_json_bytes(value) + b"\n")
        stream.flush()
    return destination


def validation_document() -> dict[str, Any]:
    return {
        "status": "VALIDATED_STATIC_B0_SHELL",
        "configuration": frozen_configuration(),
        "allowed_modes": ["validate", "readiness", "assess-run", "run-b0"],
        "refused_runs": ["CBSC-OMRC-B1-THREE-SEED-SCOUT", "CBSC-OMRC-B2-TWO-SEED-STABILITY"],
        "scientific_branch": None,
        "performance_disposition": "PILOT_ONLY",
    }


def readiness_document(implementation_commit: str | None = None) -> dict[str, Any]:
    source_receipt = None
    if implementation_commit is not None:
        source_receipt = verify_source_conformance(implementation_commit)
    source_conformant = source_receipt is not None
    return {
        "status": (
            "B0_ENGINE_SOURCE_CONFORMANT"
            if source_conformant
            else "B0_ENGINE_BOUND_SOURCE_CONFORMANCE_PENDING"
        ),
        "engine_bound": True,
        "source_conformant": source_conformant,
        "source_conformance": source_receipt,
        "engine_spec": (
            "experiments.candidates.capability_bound_semantic_currentness."
            "omrc_b01.engine:b0_engine"
        ),
        "engine_contract": "CANONICAL_FIXED_FACTORY_ONLY",
        "configuration": frozen_configuration(),
        "run_b0_authorized": source_conformant,
        "blocker": (
            None
            if source_conformant
            else "implementation commit was not supplied and source conformance is unproven"
        ),
        "scientific_branch": None,
        "performance_disposition": "PILOT_ONLY",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    validate = modes.add_parser("validate")
    validate.add_argument("--output", type=Path)
    readiness = modes.add_parser("readiness")
    readiness.add_argument("--implementation-commit")
    readiness.add_argument("--output", type=Path)
    assess = modes.add_parser("assess-run")
    assess.add_argument("--output", type=Path, required=True)
    run = modes.add_parser("run-b0")
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--implementation-commit", required=True)
    run.add_argument("--run-name", default=B0_RUN_NAME)
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
            document = readiness_document(args.implementation_commit)
            if args.output is not None:
                _write_create_only(args.output, document)
            print(json.dumps(document, indent=2, sort_keys=True))
            return 0 if document["run_b0_authorized"] else 4
        if args.mode == "assess-run":
            output = ensure_confined(args.output, CONFINED_ROOT)
            if output.exists():
                raise FileExistsError(f"create-only assess-run receipt already exists: {output}")
            output.parent.mkdir(parents=True, exist_ok=True)
            document = run_assess_preflight(
                output,
                workers=1,
                threads_per_worker=1,
            )
            print(json.dumps(document, indent=2, sort_keys=True))
            return 0 if document.get("memory_safe") is True else 6

        published = run_b0(
            final_path=args.output,
            implementation_commit=args.implementation_commit,
            run_name=args.run_name,
        )
        print(json.dumps({"published": str(published), "scientific_branch": None}, indent=2))
        return 0
    except (B0ContractError, FileExistsError, ValueError, OSError) as exc:
        print(f"CBSC OMRC B0 refused: {exc}", file=sys.stderr)
        return 6


if __name__ == "__main__":
    raise SystemExit(main())
