"""Value-blind FRRIE V2 describe, prospective-check, and guarded-run CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .contracts.core import INFERENCE_CONTRACT, ContractError, load_manifest, structural_description
from .host import NativeBackendUnavailable, NativePreflightFailed
from .lifecycle import publish_create_only
from .preflight import prospective_preflight


EXIT_INVALID_CONTRACT = 2
EXIT_MISSING_NATIVE_BACKEND = 3
EXIT_NATIVE_BUILD_REQUIRED = 4
EXIT_FAILED_PREFLIGHT = 5
EXIT_NOT_READY = 6
EXIT_TECHNICAL_FAILURE = 7
EXIT_RESUME_MISMATCH = EXIT_INVALID_CONTRACT

INFERENCE_BLOCKER = "SIMULTANEOUS_MEAN_INFERENCE_UNRESOLVED_AT_24_BLOCKS"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="finite_resource_relational_inductive_efficiency")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("describe")
    check = sub.add_parser("check")
    check.add_argument("--manifest", required=True)
    check.add_argument("--output", required=True)
    run = sub.add_parser("run")
    run.add_argument("--manifest", required=True)
    run.add_argument("--output-root", required=True)
    run.add_argument("--resume", action="store_true")
    return parser


def _load_json(path: str, field: str) -> dict[str, object]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"{field} is absent or unreadable") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{field} must be a JSON object")
    return value


def _check_exit(report: dict[str, object]) -> int:
    """Classify the prospective report without changing the published facts."""
    blockers = report.get("blockers")
    if not isinstance(blockers, list):
        raise NativePreflightFailed("prospective preflight returned no blocker list")
    if "PACKAGE_NATIVE_ARTIFACT_ABSENT" in blockers:
        return EXIT_MISSING_NATIVE_BACKEND
    if "PACKAGE_NATIVE_FRESH_BUILD_REQUIRED" in blockers:
        return EXIT_NATIVE_BUILD_REQUIRED
    if any(blocker in blockers for blocker in (
        "PACKAGE_NATIVE_ABI_UNAVAILABLE", "PACKAGE_NATIVE_CONTRACT_MISMATCH",
    )):
        return EXIT_FAILED_PREFLIGHT
    if report.get("ready") is not True:
        return EXIT_NOT_READY
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "describe":
            print(json.dumps(structural_description(), sort_keys=True))
            return 0

        # validate_manifest is the V2 gate and rejects V1 before packet, root,
        # RNG, model, native, rollout, or scientific-value activity.
        manifest = load_manifest(args.manifest)
        if args.command == "check":
            output = Path(args.output)
            bound_output = Path(manifest["preflight_receipt"]["path"])
            if output.resolve(strict=False) != bound_output.resolve(strict=False):
                raise ContractError("--output must equal the manifest preflight receipt path")
            if output.exists() or output.with_name(output.name + ".tmp").exists():
                raise ContractError("check output is create-only")
            # The bound packet is read directly.  A prewritten receipt is never
            # read; prospective_preflight performs its structural validation.
            packet = _load_json(manifest["sealed_seed_packet"]["path"], "sealed seed packet")
            report = prospective_preflight(
                manifest, packet, resource_ceiling=manifest["resource_ceiling"]
            )
            publish_create_only(output, report)
            return _check_exit(report)

        # This exact inference gate deliberately precedes output-root equality,
        # resume, RNG-root use, model construction, native admission and values.
        if manifest["inference"] == INFERENCE_CONTRACT and manifest["inference"]["status"] == INFERENCE_BLOCKER:
            print(INFERENCE_BLOCKER, file=sys.stderr)
            return EXIT_NOT_READY
        if Path(args.output_root) != Path(manifest["roots"]["output"]):
            raise ContractError("--output-root does not bind the manifest fresh root")
        raise NativePreflightFailed("V2 result activity requires a ready prospective preflight")
    except ContractError as exc:
        print(f"invalid contract: {exc}", file=sys.stderr)
        return EXIT_INVALID_CONTRACT
    except NativeBackendUnavailable as exc:
        print(f"missing native backend: {exc}", file=sys.stderr)
        return EXIT_MISSING_NATIVE_BACKEND
    except NativePreflightFailed as exc:
        print(f"failed preflight: {exc}", file=sys.stderr)
        return EXIT_FAILED_PREFLIGHT
    except OSError as exc:
        print(f"technical failure: {exc}", file=sys.stderr)
        return EXIT_TECHNICAL_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())
