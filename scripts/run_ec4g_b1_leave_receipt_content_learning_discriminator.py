"""One-shot source/manifest/claim/result runner for EC4G-B1."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.ec4g_r1.leave_receipt_content_learning_discriminator import (
    ASSIGNMENT_ID,
    CANDIDATE,
    CLAIM_PATHS,
    POOL_UNITS,
    RESOURCE_CLASS,
    bounded_technical_fixture,
    bounded_training_fixture,
    build_manifest,
    manifest_identity,
    preflight_report,
    run_treatment,
    validate_bounded_technical_fixture,
    validate_bounded_training_fixture,
    validate_manifest,
    validate_preflight,
    validate_result,
)


ROOT_MARKER = "ec4g_b1_leave_receipt_content_learning_discriminator"
MANIFEST_NAME = "frozen_manifest.json"
PROOF_NAME = "technical_proof.json"
INVOCATION_CLAIM_NAME = "registered_preflight_claim.json"
CLAIM_NAME = "registered_full_claim.json"
RESULT_NAME = "ec4g_b1_leave_receipt_content_learning_discriminator_result.json"
FAILURE_NAME = "registered_full_terminal_failure.json"


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write_once(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=True, indent=2, sort_keys=True)
            handle.write("\n")
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _require_root(path: Path) -> Path:
    root = path.resolve()
    if ROOT_MARKER not in root.name:
        raise ValueError(f"run root must be an isolated {ROOT_MARKER} directory")
    if root == PROJECT_ROOT or PROJECT_ROOT in root.parents:
        raise ValueError("run root must be outside the source checkout")
    return root


def _git(*arguments: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(PROJECT_ROOT), *arguments], text=True, encoding="utf-8"
    ).strip()


def _source_revision() -> str:
    return _git("rev-parse", "HEAD")


def _require_clean_claim_sources() -> None:
    dirty = _git("status", "--porcelain", "--", *CLAIM_PATHS)
    if dirty:
        raise ValueError("registered-full claim paths are not clean: " + dirty)


def _require_bound_manifest(manifest: Mapping[str, object]) -> dict[str, object]:
    issues = validate_manifest(manifest)
    if issues:
        raise ValueError("invalid manifest: " + "; ".join(issues))
    if manifest.get("source_revision") != _source_revision():
        raise ValueError("manifest source revision differs from bound worktree HEAD")
    return dict(manifest)


def _manifest_command(args: argparse.Namespace) -> int:
    output = args.output.resolve()
    root = _require_root(output.parent)
    if output != root / MANIFEST_NAME:
        raise ValueError(f"manifest output must be {root / MANIFEST_NAME}")
    if args.source_revision != _source_revision():
        raise ValueError("requested source revision differs from bound worktree HEAD")
    manifest = build_manifest(
        source_revision=args.source_revision,
        run_id=args.run_id,
        technical_only=args.technical_only,
    )
    _write_once(output, manifest)
    return 0


def _technical_proof_command(args: argparse.Namespace) -> int:
    root = _require_root(args.run_root)
    if args.manifest.resolve() != root / MANIFEST_NAME:
        raise ValueError(f"technical proof manifest must be {root / MANIFEST_NAME}")
    manifest = _require_bound_manifest(_read_json(args.manifest))
    if manifest.get("technical_only") is not True:
        raise ValueError("technical proof requires technical_only=true")
    preflight = preflight_report(manifest)
    fixture = bounded_technical_fixture()
    training_fixture = bounded_training_fixture()
    issues = list(validate_preflight(manifest, preflight))
    issues.extend(validate_bounded_technical_fixture(fixture))
    issues.extend(validate_bounded_training_fixture(training_fixture))
    proof = {
        "artifact_kind": "ec4g_b1_technical_proof",
        "assignment_id": ASSIGNMENT_ID,
        "manifest_identity": manifest_identity(manifest),
        "all_passed": not issues and bool(preflight["all_passed"]),
        "issues": issues,
        "preflight": preflight,
        "bounded_fixture": fixture,
        "bounded_training_fixture": training_fixture,
        "registered_paired_fulls": 0,
        "result_bearing_runs": 0,
    }
    _write_once(root / PROOF_NAME, proof)
    print(json.dumps({"status": "VALID" if proof["all_passed"] else "INVALID"}))
    return 0 if proof["all_passed"] else 2


def _registered_full_command(args: argparse.Namespace) -> int:
    root = _require_root(args.run_root)
    if Path.cwd().resolve() != PROJECT_ROOT:
        raise ValueError(
            f"registered-full cwd must be the bound source worktree {PROJECT_ROOT}"
        )
    manifest_path = (root / MANIFEST_NAME).resolve()
    if args.manifest.resolve() != manifest_path:
        raise ValueError(f"registered-full manifest must be {manifest_path}")
    manifest = _require_bound_manifest(_read_json(manifest_path))
    if manifest.get("technical_only") is not False:
        raise ValueError("registered-full requires technical_only=false")
    _require_clean_claim_sources()
    claim_path = root / CLAIM_NAME
    invocation_claim_path = root / INVOCATION_CLAIM_NAME
    result_path = root / RESULT_NAME
    failure_path = root / FAILURE_NAME
    if (
        invocation_claim_path.exists()
        or claim_path.exists()
        or result_path.exists()
        or failure_path.exists()
    ):
        raise FileExistsError("the sole registered EC4G-B1 invocation is already consumed")

    # This marker consumes the unique invocation before registered preflight.
    # A process failure or branch-1 result therefore cannot be corrected by a
    # second invocation.  The result-bearing-full claim remains separate and
    # is written only after preflight passes.
    _write_once(
        invocation_claim_path,
        {
            "artifact_kind": "ec4g_b1_registered_preflight_claim",
            "assignment_id": ASSIGNMENT_ID,
            "candidate": CANDIDATE,
            "run_id": manifest["run_id"],
            "source_revision": manifest["source_revision"],
            "manifest_identity": manifest_identity(manifest),
            "registered_paired_fulls": 0,
            "corrected_invocations_authorized": 0,
            "retry_rescue_sweep": 0,
        },
    )
    preflight = preflight_report(manifest)
    preflight_issues = validate_preflight(manifest, preflight)
    if preflight_issues or not preflight["all_passed"]:
        result = run_treatment(manifest)
        issues = validate_result(manifest, result)
        if issues:
            raise ValueError("preflight result validation failed: " + "; ".join(issues))
        _write_once(result_path, result)
        return 2

    _write_once(
        claim_path,
        {
            "artifact_kind": "ec4g_b1_registered_full_claim",
            "assignment_id": ASSIGNMENT_ID,
            "candidate": CANDIDATE,
            "resource_class": RESOURCE_CLASS,
            "pool_units": POOL_UNITS,
            "run_id": manifest["run_id"],
            "source_revision": manifest["source_revision"],
            "manifest_identity": manifest_identity(manifest),
            "canonical_result_name": RESULT_NAME,
            "registered_paired_fulls": 1,
            "retry_rescue_sweep": 0,
        },
    )
    try:
        result = run_treatment(manifest)
        issues = validate_result(manifest, result)
        if issues:
            raise ValueError("result validation failed: " + "; ".join(issues))
        _write_once(result_path, result)
    except BaseException as exc:
        _write_once(
            failure_path,
            {
                "artifact_kind": "ec4g_b1_registered_full_terminal_failure",
                "assignment_id": ASSIGNMENT_ID,
                "manifest_identity": manifest_identity(manifest),
                "exception_type": type(exc).__name__,
                "first_failure": str(exc),
                "registered_paired_fulls": 1,
                "corrected_invocations_authorized": 0,
                "retry_rescue_sweep": 0,
            },
        )
        raise
    return 0


def _validate_command(args: argparse.Namespace) -> int:
    root = _require_root(args.run_root)
    manifest = _read_json(root / MANIFEST_NAME)
    result = _read_json(root / RESULT_NAME)
    issues = validate_result(manifest, result)
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
        description="EC4G-B1 leave-receipt content learning discriminator"
    )
    commands = parser.add_subparsers(dest="command", required=True)

    manifest = commands.add_parser("manifest", help="write one immutable manifest")
    manifest.add_argument("--source-revision", required=True)
    manifest.add_argument("--run-id", required=True)
    manifest.add_argument("--technical-only", action="store_true")
    manifest.add_argument("--output", type=Path, required=True)
    manifest.set_defaults(handler=_manifest_command)

    proof = commands.add_parser(
        "technical-proof", help="run zero-full preflight and bounded host proof"
    )
    proof.add_argument("--manifest", type=Path, required=True)
    proof.add_argument("--run-root", type=Path, required=True)
    proof.set_defaults(handler=_technical_proof_command)

    full = commands.add_parser(
        "registered-full", help="consume the sole registered paired full"
    )
    full.add_argument("--manifest", type=Path, required=True)
    full.add_argument("--run-root", type=Path, required=True)
    full.set_defaults(handler=_registered_full_command)

    validate = commands.add_parser("validate", help="pure retained-result validation")
    validate.add_argument("--run-root", type=Path, required=True)
    validate.set_defaults(handler=_validate_command)
    return parser


def main() -> int:
    args = _parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
