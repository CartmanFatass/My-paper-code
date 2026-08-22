"""Small JSON boundary CLI used by explicit PowerShell wrappers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .artifact_protocol import parse_assignment, parse_result, validate_assignment, validate_result
from .constraint_lint import lint_repository
from .experiment_manifest import load_backend_registry, load_manifest, validate_manifest
from .incident_scope import ImpactEnvelope, IncidentLevel
from .intake_router import route_result
from .requirements_registry import load_requirements, render_requirements_markdown, validate_registry
from .resource_preflight import load_resource_preflight, validate_resource_preflight
from .runtime_plausibility import EstimateBasis, RuntimeSample, assess_runtime


def _out(payload: object) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=lambda item: item.value if hasattr(item, "value") else item.__dict__))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    req = sub.add_parser("requirements")
    req.add_argument("action", choices=["validate", "render", "show"])
    req.add_argument("--path", default="docs/project/PROJECT_REQUIREMENTS.toml")
    req.add_argument("--id")
    assignment = sub.add_parser("assignment")
    assignment.add_argument("path")
    assignment.add_argument("--requirements", default="docs/project/PROJECT_REQUIREMENTS.toml")
    result = sub.add_parser("result")
    result.add_argument("path")
    result.add_argument("--assignment", required=True)
    result.add_argument("--requirements", default="docs/project/PROJECT_REQUIREMENTS.toml")
    incident = sub.add_parser("incident")
    incident.add_argument("result")
    incident.add_argument("--assignment", required=True)
    incident.add_argument("--requirements", default="docs/project/PROJECT_REQUIREMENTS.toml")
    preflight = sub.add_parser("preflight")
    preflight.add_argument("path")
    manifest = sub.add_parser("manifest")
    manifest.add_argument("path")
    manifest.add_argument("--preflight", required=True)
    manifest.add_argument("--requirements", default="docs/project/PROJECT_REQUIREMENTS.toml")
    manifest.add_argument("--registry", default="docs/project/EXECUTION_BACKEND_REGISTRY.toml")
    manifest.add_argument("--project-map", default="docs/project/PROJECT_MAP.md")
    runtime = sub.add_parser("runtime")
    runtime.add_argument("path")
    lint = sub.add_parser("lint")
    lint.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    if args.command == "requirements":
        requirements = load_requirements(Path(args.path))
        if args.action == "validate":
            errors = validate_registry(requirements)
            _out({"valid": not errors, "errors": errors})
            return 1 if errors else 0
        if args.action == "render":
            print(render_requirements_markdown(requirements), end="")
            return 0
        item = requirements.get(args.id or "")
        return _out(item.__dict__ if item else {"error": "unknown requirement id"})
    if args.command == "assignment":
        item = parse_assignment(Path(args.path)); errors = validate_assignment(item, load_requirements(Path(args.requirements)))
        _out({"valid": not errors, "errors": errors, "assignment_id": item.assignment_id})
        return 1 if errors else 0
    if args.command == "result":
        item = parse_result(Path(args.path)); assignment = parse_assignment(Path(args.assignment)); errors = validate_result(item, assignment)
        _out({"valid": not errors, "errors": errors, "assignment_id": item.assignment_id})
        return 1 if errors else 0
    if args.command == "incident":
        result_item = parse_result(Path(args.result)); assignment_item = parse_assignment(Path(args.assignment)); requirements = load_requirements(Path(args.requirements));
        return _out(route_result(assignment_item, result_item, requirements).__dict__)
    if args.command == "preflight":
        item = load_resource_preflight(Path(args.path)); errors = validate_resource_preflight(item)
        hard_errors = [error for error in errors if not str(error).startswith("WARNING:")]
        _out({"valid": not hard_errors, "errors": hard_errors, "warnings": [error for error in errors if str(error).startswith("WARNING:")], "preflight_id": item.preflight_id})
        return 1 if hard_errors else 0
    if args.command == "manifest":
        item = load_manifest(Path(args.path)); pre = load_resource_preflight(Path(args.preflight)); reqs = load_requirements(Path(args.requirements)); registry = load_backend_registry(Path(args.registry)); errors = validate_manifest(item, pre, reqs, registry, Path(args.project_map))
        _out({"valid": not errors, "errors": errors, "manifest_id": item.manifest_id})
        return 1 if errors else 0
    if args.command == "runtime":
        raw = json.loads(Path(args.path).read_text(encoding="utf-8")); sample = RuntimeSample(runtime_profile=str(raw["runtime_profile"]), basis=EstimateBasis(str(raw["basis"])), environment_steps=int(raw["environment_steps"]), optimizer_updates=int(raw.get("optimizer_updates", 0)), evaluations=int(raw.get("evaluations", 0)), wall_seconds=float(raw["wall_seconds"]), backend=str(raw["backend"]), parallel=bool(raw["parallel"]), worker_count=int(raw["worker_count"]), threads_per_worker=int(raw["threads_per_worker"]), target_steps=int(raw["target_steps"])); return _out(assess_runtime(sample))
    findings = lint_repository(Path(args.root)); _out({"valid": not findings, "findings": findings}); return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
