"""Frozen support and sole BELIEF production command surface."""

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
from typing import Sequence
import json

from .contract import CONTRACT_ID, FEATURE_NAMES, TEST_ONLY_MODE, validate_contract
from .production import (
    create_production_manifest,
    preflight_production,
    run_belief,
    validate_production_preflight,
)
from .support import preflight_support, validate_support


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="ucope-contextual-paid-acquisition-r01")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("describe", help="describe the non-result implementation contract")
    check = commands.add_parser("check-contract", help="validate a frozen manifest")
    check.add_argument("--manifest", required=True)
    create = commands.add_parser("create-production-manifest", help="create the immutable PRODUCTION manifest once")
    create.add_argument("--manifest", required=True)
    support = commands.add_parser("preflight-support", help="materialize TEST_ONLY support without constructing a model")
    support.add_argument("--manifest", required=True)
    support.add_argument("--output-root", required=True)
    preflight = commands.add_parser("preflight-production", help="gate resources and atomically materialize production support")
    preflight.add_argument("--manifest", required=True)
    preflight.add_argument("--output-root", required=True)
    validate = commands.add_parser("validate-preflight", help="validate a complete support artifact")
    validate.add_argument("--artifact", required=True)
    run = commands.add_parser("run-belief", help="run the sole result-bearing BELIEF workflow")
    run.add_argument("--manifest", required=True)
    run.add_argument("--preflight", required=True)
    run.add_argument("--output-root", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "describe":
        print(json.dumps({"contract_id": CONTRACT_ID, "phase": "BELIEF", "feature_names": FEATURE_NAMES, "commands": ["describe", "check-contract", "create-production-manifest", "preflight-support", "preflight-production", "validate-preflight", "run-belief"]}, sort_keys=True))
    elif args.command == "check-contract":
        manifest = validate_contract(args.manifest)
        print(json.dumps({"valid": True, "contract_id": CONTRACT_ID, "mode": manifest["mode"]}, sort_keys=True))
    elif args.command == "create-production-manifest":
        artifact = create_production_manifest(args.manifest)
        print(json.dumps({"created": True, "manifest": str(artifact)}, sort_keys=True))
    elif args.command == "preflight-support":
        manifest = validate_contract(args.manifest)
        if manifest["mode"] != TEST_ONLY_MODE:
            raise ValueError("preflight-support is TEST_ONLY; use preflight-production for PRODUCTION")
        artifact = preflight_support(manifest, args.output_root)
        print(json.dumps({"complete": True, "artifact": str(artifact)}, sort_keys=True))
    elif args.command == "preflight-production":
        artifact = preflight_production(args.manifest, args.output_root)
        print(json.dumps({"complete": True, "artifact": str(artifact)}, sort_keys=True))
    elif args.command == "validate-preflight":
        with Path(args.artifact).open("r", encoding="utf-8") as stream:
            candidate = json.load(stream)
        value = (
            validate_production_preflight(args.artifact)
            if isinstance(candidate, dict) and candidate.get("format") == "UCOPE_CPA_PRODUCTION_RESOURCE_SUPPORT_PREFLIGHT_V2"
            else validate_support(args.artifact)
        )
        print(json.dumps({"valid": True, "complete": value["complete"]}, sort_keys=True))
    elif args.command == "run-belief":
        result = run_belief(args.manifest, args.preflight, args.output_root)
        print(json.dumps({"complete": True, "result": str(result)}, sort_keys=True))
    else:  # pragma: no cover
        raise AssertionError("unreachable command")
    return 0


__all__ = ["build_parser", "main"]
