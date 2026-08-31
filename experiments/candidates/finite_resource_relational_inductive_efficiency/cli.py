"""FRRIE describe/check/guarded-run command line."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from .contracts.core import ContractError, FIXTURE_CONTRACTS, load_manifest, structural_description
from .host import NativeBackendUnavailable, NativeContract, NativePreflightFailed
from .runner import (
    ProductionTrainingUnavailable, ResumeContractMismatch, SealedInputMissing,
    validate_sealed_seed_packet,
)
from .lifecycle import publish_create_only

EXIT_INVALID_CONTRACT = 2
EXIT_MISSING_NATIVE_BACKEND = 3
EXIT_FAILED_PREFLIGHT = 4
EXIT_RESUME_MISMATCH = 5
EXIT_TECHNICAL_FAILURE = 6


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


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "describe":
            print(json.dumps(structural_description(), sort_keys=True))
            return 0
        manifest = load_manifest(args.manifest)
        if args.command == "check":
            output = Path(args.output)
            if output.exists():
                raise ContractError("check output is create-only")
            seed_packet = _load_json(manifest["sealed_seed_packet"]["path"], "sealed seed packet")
            validate_sealed_seed_packet(seed_packet, manifest)
            preflight = _load_json(manifest["preflight_receipt"]["path"], "preflight receipt")
            host = manifest["host"]
            compute = manifest["compute"]
            expected_native = NativeContract(
                host["id"], host["source_id"], host["component"], host["abi"],
                host["binding_kind"], compute["native_width"], compute["workers"],
                compute["threads"], dtype=compute["model_dtype"],
                reduction_dtype=compute["reduction_dtype"], device=compute["device"],
                python_fallback=False, test_only=False,
            )
            expected_preflight = {
                "schema": "FRRIE_NATIVE_PREFLIGHT_V1",
                "ok": True,
                "fresh": True,
                "complete": True,
                "native_contract": asdict(expected_native),
                "resource_ceiling": manifest["resource_ceiling"],
            }
            if preflight != expected_preflight:
                raise NativePreflightFailed("preflight structure differs from the direct resource/native contract")
            fixture_dir = Path(__file__).parent / "fixtures"
            fixture_paths = {
                "ccic": fixture_dir / "ccic_control_v1.json",
                "egrcr": fixture_dir / "egrcr_control_v1.json",
                "raw_value": fixture_dir / "raw_value_v1.json",
                "vqfp": fixture_dir / "vqfp_controls_v1.json",
            }
            for name, path in fixture_paths.items():
                fixture = _load_json(str(path), f"{name} fixture")
                contract = {key: fixture[key] for key in FIXTURE_CONTRACTS[name] if key in fixture}
                if contract != FIXTURE_CONTRACTS[name]:
                    raise ContractError(f"{name} fixture does not satisfy its direct contract")
            facts = {
                "schema": "FRRIE_VALUE_BLIND_CHECK_V1",
                "contract_valid": True,
                "sealed_packet_structurally_complete": True,
                "preflight_structurally_complete": True,
                "native_callable_available": False,
                "ready_for_result_activity": False,
                "scientific_values_read": False,
            }
            publish_create_only(output, facts)
            return EXIT_MISSING_NATIVE_BACKEND
        if Path(args.output_root) != Path(manifest["roots"]["output"]):
            raise ContractError("--output-root does not bind the manifest fresh root")
        # No fresh FRRIE ctypes function or production trainer is bundled.
        raise NativeBackendUnavailable("fresh FRRIE native backend is not installed")
    except ResumeContractMismatch as exc:
        print(f"resume mismatch: {exc}", file=sys.stderr)
        return EXIT_RESUME_MISMATCH
    except (ContractError, SealedInputMissing) as exc:
        print(f"invalid contract: {exc}", file=sys.stderr)
        return EXIT_INVALID_CONTRACT
    except NativeBackendUnavailable as exc:
        print(f"missing native backend: {exc}", file=sys.stderr)
        return EXIT_MISSING_NATIVE_BACKEND
    except NativePreflightFailed as exc:
        print(f"failed preflight: {exc}", file=sys.stderr)
        return EXIT_FAILED_PREFLIGHT
    except (ProductionTrainingUnavailable, OSError, RuntimeError) as exc:
        print(f"technical failure: {exc}", file=sys.stderr)
        return EXIT_TECHNICAL_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())
