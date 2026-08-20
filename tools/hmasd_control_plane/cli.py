"""Command-line entry point for read-only diagnostics and simple long effects."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


COMPONENTS = (
    "semantic",
    "supervisor",
    "agentify",
    "long-effect",
    "research-events",
    "mcp-runtime",
)


def _diagnostic_parser(name: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--component", choices=COMPONENTS)
    parser.add_argument("--since")
    parser.add_argument("--output")
    parser.add_argument("--experiment-root", action="append", default=[])
    return parser


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hmasd-control-plane")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("doctor", parents=[_diagnostic_parser("doctor")])
    subcommands.add_parser("incidents", parents=[_diagnostic_parser("incidents")])

    long_effect = subcommands.add_parser("long-effect")
    long_effect_commands = long_effect.add_subparsers(
        dest="long_effect_command", required=True
    )
    run = long_effect_commands.add_parser("run")
    run.add_argument("--spec", required=True)
    run.add_argument("--run-root", required=True)
    observe = long_effect_commands.add_parser("observe")
    observe.add_argument("--run-root", required=True)
    return parser


def _json_text(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _text_render(payload: object) -> str:
    if not isinstance(payload, dict):
        return _json_text(payload)
    lines: list[str] = []
    schema = payload.get("schema")
    if schema:
        lines.append(str(schema))
    if payload.get("status"):
        lines.append(f"status: {payload['status']}")
    findings = payload.get("findings")
    if isinstance(findings, list):
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            lines.append(
                "[{severity}] {component} {exact_object}: {observed_fact}".format(
                    severity=finding.get("severity", "INFO"),
                    component=finding.get("component", "unknown"),
                    exact_object=finding.get("exact_object", "unknown"),
                    observed_fact=finding.get("observed_fact", ""),
                )
            )
    incidents = payload.get("incidents")
    if isinstance(incidents, list):
        for incident in incidents:
            if not isinstance(incident, dict):
                continue
            lines.append(
                "[{component}] {incident_id} {exact_object}: {observed_fact}".format(
                    component=incident.get("component", "unknown"),
                    incident_id=incident.get("incident_id", "unknown"),
                    exact_object=incident.get("exact_object", "unknown"),
                    observed_fact=incident.get("observed_fact", ""),
                )
            )
    return "\n".join(lines) + "\n"


def _runtime_output_path(repo_root: Path, raw_output: str) -> Path:
    runtime_root = (repo_root / "runtime").resolve()
    output = Path(raw_output).resolve()
    try:
        output.relative_to(runtime_root)
    except ValueError as exc:
        raise ValueError("--output must be inside <repo-root>/runtime") from exc
    if output.suffix.lower() != ".json":
        raise ValueError("--output must name a JSON file")
    return output


def _write_runtime_snapshot(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(_json_text(payload))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _diagnostic_call(args: argparse.Namespace) -> tuple[object, int]:
    from .diagnostics import collect_doctor, collect_incidents

    keyword_args = {
        "component": args.component,
        "since": args.since,
        "experiment_roots": tuple(Path(item) for item in args.experiment_root),
    }
    if args.command == "doctor":
        return collect_doctor(Path(args.repo_root), **keyword_args)
    incidents, exit_code = collect_incidents(Path(args.repo_root), **keyword_args)
    return (
        {
            "schema": "HMASD_CONTROL_PLANE_INCIDENT_INDEX_V1",
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "incidents": incidents,
        },
        exit_code,
    )


def _dispatch(args: argparse.Namespace) -> tuple[object, int]:
    if args.command in {"doctor", "incidents"}:
        payload, exit_code = _diagnostic_call(args)
        if args.output:
            _write_runtime_snapshot(
                _runtime_output_path(Path(args.repo_root), args.output), payload
            )
        return payload, exit_code
    from .long_effect import observe_run, run_effect

    if args.long_effect_command == "run":
        return run_effect(Path(args.spec), Path(args.run_root)), 0
    return observe_run(Path(args.run_root)), 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        payload, exit_code = _dispatch(args)
        output_format = getattr(args, "format", "json")
        sys.stdout.write(_text_render(payload) if output_format == "text" else _json_text(payload))
        return int(exit_code)
    except Exception as exc:
        sys.stderr.write(
            _json_text(
                {
                    "error": type(exc).__name__,
                    "message": str(exc),
                }
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
