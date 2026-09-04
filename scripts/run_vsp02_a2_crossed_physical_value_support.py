"""Thin one-shot CLI for the deterministic VSP02-A2 value certificate."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.vsp_02.crossed_physical_value_support import (
    A2_ASSIGNMENT_ID,
    A2_CANDIDATE,
    build_a2_manifest,
    json_ready,
    run_a2_probe,
    validate_a2_artifact,
    validate_a2_manifest,
)


CLAIM_PATHS = (
    "experiments/candidates/vsp_02/crossed_physical_value_support.py",
    "scripts/run_vsp02_a2_crossed_physical_value_support.py",
    "tests/experiments/candidates/vsp_02/test_crossed_physical_value_support.py",
    "docs/research/candidates/vsp_02/CODE_SCIENCE_INDEX.md",
)
RUNTIME_DEPENDENCY_PATHS = (
    "experiments/candidates/vsp_02/owner_action_responsive_lifecycle.py",
)
REGISTERED_SOURCE_PATHS = CLAIM_PATHS + RUNTIME_DEPENDENCY_PATHS
REGISTERED_CLAIM_NAME = "registered_claim.json"
REGISTERED_RESULT_NAME = "raw_result.json"


def _read_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _json_bytes(payload: object) -> bytes:
    return json.dumps(
        json_ready(payload), ensure_ascii=True, indent=2, sort_keys=True
    ).encode("utf-8") + b"\n"


def _write_once(path: Path, payload: object) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite one-shot artifact: {path}")
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="xb", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            temporary = handle.name
            handle.write(_json_bytes(payload))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def _exclusive_claim(path: Path, payload: object) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(_json_bytes(payload))
        handle.flush()
        os.fsync(handle.fileno())


def _current_source_revision() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _require_source_revision(manifest: object) -> None:
    if not isinstance(manifest, dict):
        return
    actual = _current_source_revision()
    if manifest.get("source_revision") != actual:
        raise ValueError(
            f"manifest source_revision {manifest.get('source_revision')!r} "
            f"does not match checkout HEAD {actual}"
        )


def _require_clean_registered_sources() -> None:
    tracked = tuple(
        sorted(
            subprocess.run(
                ["git", "ls-files", "--", *REGISTERED_SOURCE_PATHS],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.splitlines()
        )
    )
    expected = tuple(sorted(REGISTERED_SOURCE_PATHS))
    if tracked != expected:
        raise ValueError(
            "registered claim source is untracked or absent: "
            f"{sorted(set(expected) - set(tracked))}"
        )
    dirty = subprocess.run(
        [
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            *REGISTERED_SOURCE_PATHS,
        ],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    if dirty:
        raise ValueError(f"registered claim source differs from HEAD: {dirty}")


def _manifest_command(args: argparse.Namespace) -> int:
    actual_revision = _current_source_revision()
    if args.source_revision != actual_revision:
        raise ValueError(
            f"source_revision {args.source_revision!r} does not match checkout HEAD {actual_revision}"
        )
    manifest = build_a2_manifest(
        source_revision=args.source_revision,
        run_id=args.run_id,
        technical_only=args.technical_only,
    )
    issues = validate_a2_manifest(manifest)
    if issues:
        raise ValueError("; ".join(issues))
    _write_once(args.output, manifest)
    return 0


def _exercise_command(args: argparse.Namespace) -> int:
    manifest = _read_json(args.manifest)
    _require_source_revision(manifest)
    if not isinstance(manifest, dict) or manifest.get("technical_only") is not True:
        raise ValueError("exercise requires technical_only=true")
    artifact = run_a2_probe(manifest)
    issues = validate_a2_artifact(artifact)
    if issues:
        raise ValueError("; ".join(issues))
    _write_once(args.output, artifact)
    return 0


def _registered_audit_command(args: argparse.Namespace) -> int:
    manifest = _read_json(args.manifest)
    _require_source_revision(manifest)
    _require_clean_registered_sources()
    if not isinstance(manifest, dict) or manifest.get("technical_only") is not False:
        raise ValueError("registered-audit requires technical_only=false")
    issues = validate_a2_manifest(manifest)
    if issues:
        raise ValueError("; ".join(issues))
    run_root = args.run_root.resolve()
    claim_path = run_root / REGISTERED_CLAIM_NAME
    result_path = run_root / REGISTERED_RESULT_NAME
    if claim_path.exists() or result_path.exists():
        raise FileExistsError("registered A2 invocation is already claimed")
    _exclusive_claim(
        claim_path,
        {
            "artifact_kind": "vsp02_a2_registered_run_claim",
            "assignment_id": A2_ASSIGNMENT_ID,
            "candidate": A2_CANDIDATE,
            "run_id": manifest["run_id"],
            "source_revision": manifest["source_revision"],
            "canonical_result_name": REGISTERED_RESULT_NAME,
            "retry_permitted": False,
        },
    )
    # The invocation is consumed once the claim exists; later failure is terminal.
    artifact = run_a2_probe(manifest)
    artifact_issues = validate_a2_artifact(artifact)
    if artifact_issues:
        raise ValueError("; ".join(artifact_issues))
    _write_once(result_path, artifact)
    return 0


def _validate_command(args: argparse.Namespace) -> int:
    artifact = _read_json(args.artifact)
    if isinstance(artifact, dict):
        _require_source_revision(artifact.get("manifest"))
    issues = validate_a2_artifact(artifact)
    print(
        json.dumps(
            {"status": "VALID" if not issues else "INVALID", "issues": list(issues)},
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0 if not issues else 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="VSP02-A2 deterministic crossed physical-value support certificate"
    )
    commands = parser.add_subparsers(dest="command", required=True)

    manifest = commands.add_parser("manifest", help="freeze one prospective immutable manifest")
    manifest.add_argument("--source-revision", required=True)
    manifest.add_argument("--run-id", required=True)
    manifest.add_argument("--technical-only", action="store_true")
    manifest.add_argument("--output", type=Path, required=True)
    manifest.set_defaults(handler=_manifest_command)

    exercise = commands.add_parser(
        "exercise", help="construct a technical artifact without consuming the registered audit"
    )
    exercise.add_argument("--manifest", type=Path, required=True)
    exercise.add_argument("--output", type=Path, required=True)
    exercise.set_defaults(handler=_exercise_command)

    audit = commands.add_parser(
        "registered-audit", help="consume the unique registered deterministic A2 audit"
    )
    audit.add_argument("--manifest", type=Path, required=True)
    audit.add_argument("--run-root", type=Path, required=True)
    audit.set_defaults(handler=_registered_audit_command)

    validate = commands.add_parser("validate", help="validate one frozen result artifact")
    validate.add_argument("--artifact", type=Path, required=True)
    validate.set_defaults(handler=_validate_command)
    return parser


def main() -> int:
    args = _parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
