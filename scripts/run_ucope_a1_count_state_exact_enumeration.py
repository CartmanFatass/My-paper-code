"""Thin one-shot CLI for the UCOPE-A1 exact-rational probe."""

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

from experiments.candidates.ucope.exact_enumerator import (
    A1_ASSIGNMENT_ID,
    A1_CANDIDATE,
    build_a1_manifest,
    run_a1_probe,
    validate_a1_artifact,
    validate_a1_manifest,
    zero_activity,
)


CLAIM_PATHS = (
    "experiments/candidates/ucope/exact_enumerator.py",
    "scripts/run_ucope_a1_count_state_exact_enumeration.py",
    "tests/experiments/candidates/ucope/test_exact_enumerator.py",
    "docs/research/candidates/ucope/CODE_SCIENCE_INDEX.md",
)
REGISTERED_CLAIM_NAME = "registered_claim.json"
REGISTERED_RESULT_NAME = "raw_result.json"


def _read_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _current_source_revision() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _require_current_source(manifest: object) -> None:
    if not isinstance(manifest, dict):
        return
    declared = manifest.get("source_revision")
    actual = _current_source_revision()
    if declared != actual:
        raise ValueError(
            f"manifest source_revision {declared!r} does not match checkout HEAD {actual}"
        )


def _git_claim_source_state() -> tuple[tuple[str, ...], tuple[str, ...]]:
    tracked = subprocess.run(
        ["git", "ls-files", "--", *CLAIM_PATHS],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    dirty = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all", "--", *CLAIM_PATHS],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    return tuple(sorted(tracked)), tuple(dirty)


def _require_clean_claim_sources() -> None:
    tracked, dirty = _git_claim_source_state()
    expected = tuple(sorted(CLAIM_PATHS))
    if tracked != expected:
        missing = sorted(set(expected) - set(tracked))
        raise ValueError(f"registered claim source is untracked or absent: {missing}")
    if dirty:
        raise ValueError(f"registered claim source differs from HEAD: {list(dirty)}")


def _write_once(path: Path, payload: object) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite one-shot artifact: {path}")
    raw = json.dumps(
        payload, ensure_ascii=True, indent=2, sort_keys=True
    ).encode("utf-8") + b"\n"
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="xb", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            temporary = handle.name
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def _create_claim_once(path: Path, payload: object) -> None:
    """Acquire the run claim with an OS-exclusive create; partial means claimed."""

    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(
        payload, ensure_ascii=True, indent=2, sort_keys=True
    ).encode("utf-8") + b"\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())


def _claim_registered_run(run_root: Path, manifest: dict[str, object]) -> Path:
    run_root = run_root.resolve()
    claim_path = run_root / REGISTERED_CLAIM_NAME
    result_path = run_root / REGISTERED_RESULT_NAME
    if claim_path.exists():
        raise FileExistsError(f"registered run is already claimed: {claim_path}")
    if result_path.exists():
        raise FileExistsError(f"canonical registered result already exists: {result_path}")
    claim = {
        "artifact_kind": "ucope_a1_registered_run_claim",
        "assignment_id": A1_ASSIGNMENT_ID,
        "candidate": A1_CANDIDATE,
        "run_id": manifest["run_id"],
        "source_revision": manifest["source_revision"],
        "canonical_result_name": REGISTERED_RESULT_NAME,
    }
    _create_claim_once(claim_path, claim)
    return result_path


def _manifest_command(args: argparse.Namespace) -> int:
    actual_revision = _current_source_revision()
    if args.source_revision != actual_revision:
        raise ValueError(
            f"source_revision {args.source_revision!r} does not match checkout HEAD {actual_revision}"
        )
    manifest = build_a1_manifest(
        source_revision=args.source_revision,
        run_id=args.run_id,
        technical_only=args.technical_only,
    )
    issues = validate_a1_manifest(manifest)
    if issues:
        raise ValueError("; ".join(issues))
    _write_once(args.output, manifest)
    return 0


def _exercise_command(args: argparse.Namespace) -> int:
    manifest = _read_json(args.manifest)
    _require_current_source(manifest)
    if not isinstance(manifest, dict) or manifest.get("technical_only") is not True:
        raise ValueError("exercise requires a technical_only=true manifest")
    artifact = run_a1_probe(manifest)
    issues = validate_a1_artifact(artifact)
    if issues:
        raise ValueError("; ".join(issues))
    _write_once(args.output, artifact)
    return 0


def _registered_probe_command(args: argparse.Namespace) -> int:
    manifest = _read_json(args.manifest)
    _require_current_source(manifest)
    _require_clean_claim_sources()
    if isinstance(manifest, dict) and manifest.get("technical_only") is True:
        raise ValueError("registered-probe rejects technical-only manifests")
    manifest_issues = validate_a1_manifest(manifest)
    if manifest_issues:
        raise ValueError("; ".join(manifest_issues))
    assert isinstance(manifest, dict)
    result_path = _claim_registered_run(args.run_root, manifest)
    # Claim now exists: all subsequent failures are terminal and cannot retry.
    artifact = run_a1_probe(manifest, activity=zero_activity())
    issues = validate_a1_artifact(artifact)
    if issues:
        raise ValueError("; ".join(issues))
    _write_once(result_path, artifact)
    return 0


def _validate_command(args: argparse.Namespace) -> int:
    artifact = _read_json(args.artifact)
    if isinstance(artifact, dict):
        _require_current_source(artifact.get("manifest"))
    issues = validate_a1_artifact(artifact)
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
        description="UCOPE-A1 exact-rational manifest and one-shot probe lifecycle"
    )
    commands = parser.add_subparsers(dest="command", required=True)

    manifest = commands.add_parser("manifest", help="freeze an immutable manifest")
    manifest.add_argument("--source-revision", required=True)
    manifest.add_argument("--run-id", required=True)
    manifest.add_argument("--technical-only", action="store_true")
    manifest.add_argument("--output", type=Path, required=True)
    manifest.set_defaults(handler=_manifest_command)

    exercise = commands.add_parser(
        "exercise", help="exercise artifact I/O without admitting a scientific terminal"
    )
    exercise.add_argument("--manifest", type=Path, required=True)
    exercise.add_argument("--output", type=Path, required=True)
    exercise.set_defaults(handler=_exercise_command)

    probe = commands.add_parser(
        "registered-probe", help="execute the single frozen result-bearing enumeration"
    )
    probe.add_argument("--manifest", type=Path, required=True)
    probe.add_argument("--run-root", type=Path, required=True)
    probe.set_defaults(handler=_registered_probe_command)

    validate = commands.add_parser("validate", help="validate a frozen artifact")
    validate.add_argument("--artifact", type=Path, required=True)
    validate.set_defaults(handler=_validate_command)
    return parser


def main() -> int:
    args = _parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
