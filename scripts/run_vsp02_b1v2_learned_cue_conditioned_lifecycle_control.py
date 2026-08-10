"""One-shot artifact lifecycle for VSP02-B1V2."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.vsp_02.learned_cue_conditioned_lifecycle_control_v2 import (
    B1_ASSIGNMENT_ID,
    B1_CANDIDATE,
    B1_RESOURCE_CLASS,
    build_manifest,
    compute_analysis,
    json_ready,
    manifest_identity,
    run_evaluation,
    run_training,
    validate_analysis_artifact,
    validate_artifact_bundle,
    validate_evaluation_artifact,
    validate_manifest,
    validate_training_artifact,
)


CLAIM_PATHS = (
    "experiments/candidates/vsp_02/learned_cue_conditioned_lifecycle_control_v2.py",
    "experiments/candidates/vsp_02/owner_action_responsive_lifecycle.py",
    "scripts/run_vsp02_b1v2_learned_cue_conditioned_lifecycle_control.py",
    "tests/experiments/candidates/vsp_02/test_learned_cue_conditioned_lifecycle_control_v2.py",
    "docs/research/candidates/vsp_02/VSP02_B1V2_CODE_SCIENCE_INDEX.md",
)
ROOT_MARKER = "vsp02_b1v2_learned_cue_conditioned_lifecycle_control"
MANIFEST_NAME = "frozen_manifest.json"
CLAIM_NAME = "registered_claim.json"
TRAINING_NAME = "training.json"
EVALUATION_NAME = "evaluation.json"
ANALYSIS_NAME = "analysis.json"
RESULT_NAME = "raw_result.json"
PHASE_NAMES = (TRAINING_NAME, EVALUATION_NAME, ANALYSIS_NAME, RESULT_NAME)


def _read_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _encoded(payload: object) -> bytes:
    return json.dumps(
        json_ready(payload), ensure_ascii=True, indent=2, sort_keys=True
    ).encode("utf-8") + b"\n"


def _write_once(path: Path, payload: object) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite write-once artifact: {path}")
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="xb", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            temporary = handle.name
            handle.write(_encoded(payload))
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
        handle.write(_encoded(payload))
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


def _require_manifest_revision(manifest: object) -> None:
    if not isinstance(manifest, Mapping):
        raise ValueError("manifest is not an object")
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
                ["git", "ls-files", "--", *CLAIM_PATHS],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.splitlines()
        )
    )
    expected = tuple(sorted(CLAIM_PATHS))
    if tracked != expected:
        raise ValueError(
            "registered claim source is untracked or absent: "
            f"{sorted(set(expected) - set(tracked))}"
        )
    dirty = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all", "--", *CLAIM_PATHS],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    if dirty:
        raise ValueError(f"registered claim source differs from HEAD: {dirty}")


def _require_root(run_root: Path) -> Path:
    root = run_root.resolve()
    if ROOT_MARKER not in str(root).lower():
        raise ValueError(f"run root must contain assignment marker {ROOT_MARKER!r}")
    return root


def _require_fresh_phase_paths(root: Path) -> None:
    existing = [name for name in PHASE_NAMES if (root / name).exists()]
    if existing:
        raise FileExistsError(f"artifact lifecycle is already materialized: {existing}")


def _result_payload(
    manifest: Mapping[str, object], analysis: Mapping[str, object]
) -> dict[str, object]:
    return {
        "artifact_kind": "vsp02_b1v2_result",
        "assignment_id": B1_ASSIGNMENT_ID,
        "candidate": B1_CANDIDATE,
        "manifest_identity": manifest_identity(manifest),
        "technical_only": manifest["technical_only"],
        "admission": analysis["admission"],
        "branch": analysis["branch"],
        "analysis_artifact": ANALYSIS_NAME,
        "strongest_technical_limitation": (
            "The fixed host has one transient cue, one decision boundary, one fixed "
            "partner, and held-out owner epochs; it supplies no transfer or long-horizon claim."
        ),
        "nonclaims": [
            "escrow or recurrent superiority",
            "long-horizon credit",
            "multi-boundary adaptation",
            "partner learning or transfer",
            "promotion, retirement, C, or formal claims",
        ],
    }


def _run_phases(root: Path, manifest: Mapping[str, object]) -> None:
    _require_fresh_phase_paths(root)
    training = run_training(manifest)
    issues = validate_training_artifact(manifest, training)
    if issues:
        raise ValueError("training validation failed: " + "; ".join(issues))
    _write_once(root / TRAINING_NAME, training)

    evaluation = run_evaluation(manifest, training, training_validated=True)
    issues = validate_evaluation_artifact(manifest, training, evaluation)
    if issues:
        raise ValueError("evaluation validation failed: " + "; ".join(issues))
    _write_once(root / EVALUATION_NAME, evaluation)

    analysis = compute_analysis(manifest, training, evaluation)
    issues = validate_analysis_artifact(manifest, training, evaluation, analysis)
    if issues:
        raise ValueError("analysis validation failed: " + "; ".join(issues))
    _write_once(root / ANALYSIS_NAME, analysis)
    _write_once(root / RESULT_NAME, _result_payload(manifest, analysis))


def _manifest_command(args: argparse.Namespace) -> int:
    actual = _current_source_revision()
    if args.source_revision != actual:
        raise ValueError(
            f"source_revision {args.source_revision!r} does not match checkout HEAD {actual}"
        )
    manifest = build_manifest(
        source_revision=args.source_revision,
        run_id=args.run_id,
        technical_only=args.technical_only,
    )
    issues = validate_manifest(manifest)
    if issues:
        raise ValueError("; ".join(issues))
    _write_once(args.output, manifest)
    return 0


def _exercise_command(args: argparse.Namespace) -> int:
    root = _require_root(args.run_root)
    manifest_path = (root / MANIFEST_NAME).resolve()
    if args.manifest.resolve() != manifest_path:
        raise ValueError(f"exercise manifest must be {manifest_path}")
    manifest = _read_json(manifest_path)
    _require_manifest_revision(manifest)
    if not isinstance(manifest, Mapping) or manifest.get("technical_only") is not True:
        raise ValueError("exercise requires technical_only=true")
    _run_phases(root, manifest)
    return 0


def _registered_full_command(args: argparse.Namespace) -> int:
    root = _require_root(args.run_root)
    manifest_path = (root / MANIFEST_NAME).resolve()
    if args.manifest.resolve() != manifest_path:
        raise ValueError(f"registered-full manifest must be {manifest_path}")
    manifest = _read_json(manifest_path)
    _require_manifest_revision(manifest)
    _require_clean_registered_sources()
    if not isinstance(manifest, Mapping) or manifest.get("technical_only") is not False:
        raise ValueError("registered-full requires technical_only=false")
    issues = validate_manifest(manifest)
    if issues:
        raise ValueError("; ".join(issues))
    claim_path = root / CLAIM_NAME
    if claim_path.exists() or any((root / name).exists() for name in PHASE_NAMES):
        raise FileExistsError("the sole registered B1V2 full is already claimed")
    _exclusive_claim(
        claim_path,
        {
            "artifact_kind": "vsp02_b1v2_registered_full_claim",
            "assignment_id": B1_ASSIGNMENT_ID,
            "candidate": B1_CANDIDATE,
            "resource_class": B1_RESOURCE_CLASS,
            "pool_units": 1,
            "run_id": manifest["run_id"],
            "source_revision": manifest["source_revision"],
            "manifest_identity": manifest_identity(manifest),
            "canonical_result_name": RESULT_NAME,
            "retry_rescue_sweep": 0,
        },
    )
    # The registered invocation is consumed from this point.  No phase retries.
    _run_phases(root, manifest)
    return 0


def _validate_command(args: argparse.Namespace) -> int:
    root = _require_root(args.run_root)
    manifest = _read_json(root / MANIFEST_NAME)
    training = _read_json(root / TRAINING_NAME)
    evaluation = _read_json(root / EVALUATION_NAME)
    analysis = _read_json(root / ANALYSIS_NAME)
    result = _read_json(root / RESULT_NAME)
    issues = list(validate_artifact_bundle(manifest, training, evaluation, analysis))
    if isinstance(manifest, Mapping) and isinstance(analysis, Mapping):
        expected_result = _result_payload(manifest, analysis)
        if json_ready(result) != json_ready(expected_result):
            issues.append("result differs from validated analysis projection")
    else:
        issues.append("result dependencies are not objects")
    print(
        json.dumps(
            {"status": "VALID" if not issues else "INVALID", "issues": issues},
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0 if not issues else 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="VSP02-B1V2 learned cue-conditioned lifecycle control"
    )
    commands = parser.add_subparsers(dest="command", required=True)

    manifest = commands.add_parser("manifest", help="write one immutable manifest")
    manifest.add_argument("--source-revision", required=True)
    manifest.add_argument("--run-id", required=True)
    manifest.add_argument("--technical-only", action="store_true")
    manifest.add_argument("--output", type=Path, required=True)
    manifest.set_defaults(handler=_manifest_command)

    exercise = commands.add_parser(
        "exercise",
        help="run the one optional reduced, branch-null, nonadmitted technical lifecycle",
    )
    exercise.add_argument("--manifest", type=Path, required=True)
    exercise.add_argument("--run-root", type=Path, required=True)
    exercise.set_defaults(handler=_exercise_command)

    registered = commands.add_parser(
        "registered-full", help="consume the sole registered full train/evaluate/analyze lifecycle"
    )
    registered.add_argument("--manifest", type=Path, required=True)
    registered.add_argument("--run-root", type=Path, required=True)
    registered.set_defaults(handler=_registered_full_command)

    validate = commands.add_parser("validate", help="independently validate retained artifacts")
    validate.add_argument("--run-root", type=Path, required=True)
    validate.set_defaults(handler=_validate_command)
    return parser


def main() -> int:
    args = _parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
