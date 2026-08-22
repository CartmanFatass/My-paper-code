"""Command line adapter for the exact RCLE-TBCFV r04 empirical runner."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from .empirical_runner import (
    EmpiricalRunnerError,
    analyze_complete_panel,
    coordinate_proposal,
    execute_full_panel,
    make_resource_request,
    read_admission_files,
    read_source_repair_admission_files,
    result_blind_preactivity_summary,
)
from .empirical_contract import EmpiricalContractError, LeaseError, canonical_json_bytes
from .empirical_artifacts import EmpiricalArtifactError


def _read(path: Path, label: str) -> dict[str, object]:
    payload = path.read_bytes()
    value = json.loads(payload.decode("ascii"))
    if not isinstance(value, dict) or canonical_json_bytes(value) != payload:
        raise EmpiricalRunnerError(f"{label} is not canonical ASCII JSON")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rcle-tbcfv-r04")
    commands = parser.add_subparsers(dest="command", required=True)
    preflight = commands.add_parser("preflight")
    preflight.add_argument("--certificate", type=Path, required=True)
    preflight.add_argument("--accepted-binding", type=Path, required=True)
    preflight.add_argument("--temp-root", type=Path, required=True)
    proposal = commands.add_parser("coordinate-proposal")
    proposal.set_defaults()
    request = commands.add_parser("resource-request")
    request.add_argument("--certificate", type=Path, required=True)
    request.add_argument("--result-root", type=Path, required=True)
    for name in ("run", "analyze"):
        command = commands.add_parser(name)
        command.add_argument("--certificate", type=Path, required=True)
        command.add_argument("--accepted-binding", type=Path, required=True)
        command.add_argument("--resource-request", type=Path, required=True)
        command.add_argument("--lease", type=Path, required=True)
        command.add_argument("--predecessor-lease", type=Path, action="append", default=[])
        command.add_argument("--coordinate-binding", type=Path, required=True)
        command.add_argument("--result-root", type=Path, required=True)
    repair = commands.add_parser("repair-resume")
    repair.add_argument("--predecessor-certificate", type=Path, required=True)
    repair.add_argument("--predecessor-accepted-binding", type=Path, required=True)
    repair.add_argument("--predecessor-resource-request", type=Path, required=True)
    repair.add_argument("--predecessor-lease", type=Path, required=True)
    repair.add_argument("--certificate", type=Path, required=True)
    repair.add_argument("--accepted-binding", type=Path, required=True)
    repair.add_argument("--resource-request", type=Path, required=True)
    repair.add_argument("--lease", type=Path, required=True)
    repair.add_argument("--repair-transition", type=Path, required=True)
    repair.add_argument("--run-identity", type=Path, required=True)
    repair.add_argument("--failed-terminal", type=Path, required=True)
    repair.add_argument("--result-root", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "coordinate-proposal":
            output = coordinate_proposal()
        elif args.command == "resource-request":
            output = make_resource_request(
                _read(args.certificate, "preactivity certificate"),
                result_root=args.result_root,
            )
        elif args.command == "preflight":
            output = result_blind_preactivity_summary(
                _read(args.certificate, "preactivity certificate"),
                _read(args.accepted_binding, "accepted binding"),
                temp_root=args.temp_root,
            )
        elif args.command == "repair-resume":
            now = datetime.now(timezone.utc)
            authority = read_source_repair_admission_files(
                predecessor_certificate_path=args.predecessor_certificate,
                predecessor_accepted_binding_path=args.predecessor_accepted_binding,
                predecessor_resource_request_path=args.predecessor_resource_request,
                predecessor_lease_path=args.predecessor_lease,
                certificate_path=args.certificate,
                accepted_binding_path=args.accepted_binding,
                resource_request_path=args.resource_request,
                lease_path=args.lease,
                repair_transition_path=args.repair_transition,
                run_identity_path=args.run_identity,
                failed_terminal_path=args.failed_terminal,
                result_root=args.result_root,
                now=now,
            )
            output = execute_full_panel(authority, now=now)
        else:
            now = datetime.now(timezone.utc)
            authority = read_admission_files(
                certificate_path=args.certificate,
                accepted_binding_path=args.accepted_binding,
                resource_request_path=args.resource_request,
                lease_path=args.lease,
                coordinate_binding_path=args.coordinate_binding,
                result_root=args.result_root,
                now=now,
                predecessor_lease_paths=args.predecessor_lease,
            )
            output = (
                execute_full_panel(authority, now=now)
                if args.command == "run"
                else analyze_complete_panel(authority, now=now)
            )
        print(json.dumps(output, sort_keys=True, separators=(",", ":")))
        return 0
    except (
        EmpiricalArtifactError,
        EmpiricalContractError,
        EmpiricalRunnerError,
        FileExistsError,
        FileNotFoundError,
        json.JSONDecodeError,
        LeaseError,
        OSError,
        TypeError,
        UnicodeDecodeError,
        ValueError,
    ) as exc:
        print(f"FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
