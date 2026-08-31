"""Non-result CLI. Training/evaluation/publication are intentionally unregistered."""

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
from typing import Sequence
import json

from .contract import CONTRACT_ID, FEATURE_NAMES, validate_contract
from .support import preflight_support, validate_support


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="ucope-contextual-paid-acquisition-r01")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("describe", help="describe the non-result implementation contract")
    check = commands.add_parser("check-contract", help="validate a frozen manifest")
    check.add_argument("--manifest", required=True)
    preflight = commands.add_parser("preflight-support", help="materialize support without constructing a model")
    preflight.add_argument("--manifest", required=True)
    preflight.add_argument("--output-root", required=True)
    validate = commands.add_parser("validate-preflight", help="validate a complete support artifact")
    validate.add_argument("--artifact", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "describe":
        print(json.dumps({"contract_id": CONTRACT_ID, "phase": "BELIEF", "feature_names": FEATURE_NAMES, "commands": ["describe", "check-contract", "preflight-support", "validate-preflight"]}, sort_keys=True))
    elif args.command == "check-contract":
        manifest = validate_contract(args.manifest)
        print(json.dumps({"valid": True, "contract_id": CONTRACT_ID, "mode": manifest["mode"]}, sort_keys=True))
    elif args.command == "preflight-support":
        artifact = preflight_support(args.manifest, args.output_root)
        print(json.dumps({"complete": True, "artifact": str(artifact)}, sort_keys=True))
    elif args.command == "validate-preflight":
        value = validate_support(args.artifact)
        print(json.dumps({"valid": True, "complete": value["complete"]}, sort_keys=True))
    else:  # pragma: no cover
        raise AssertionError("unreachable command")
    return 0


__all__ = ["build_parser", "main"]
