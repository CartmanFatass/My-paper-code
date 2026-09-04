"""One-shot artifact lifecycle for VSP02-B2."""

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

from experiments.candidates.vsp_02.vsp02_b2_paired_shadow_learner_localization import (
    B2_ASSIGNMENT_ID,
    B2_CANDIDATE,
    B2_CLAIM_PATHS,
    B2_POOL_UNITS,
    B2_RESOURCE_CLASS,
    build_manifest,
    json_ready,
    manifest_identity,
    preflight_report,
    run_treatment,
    validate_manifest,
    validate_result,
)


ROOT_MARKER = "vsp02_b2_paired_shadow_learner_localization"
MANIFEST_NAME = "frozen_manifest.json"
CLAIM_NAME = "registered_full_claim.json"
PROOF_NAME = "technical_proof.json"
RESULT_NAME = "raw_result.json"


def _read_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _encoded(payload: object) -> bytes:
    return json.dumps(
        json_ready(payload), ensure_ascii=True, indent=2, sort_keys=True
    ).encode("utf-8") + b"\n"


def _write_once(path: Path, payload: object) -> None:
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(f"refusing to overwrite write-once artifact: {target}")
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="xb", dir=target.parent, prefix=f".{target.name}.", delete=False
        ) as handle:
            temporary = handle.name
            handle.write(_encoded(payload))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def _exclusive_claim(path: Path, payload: object) -> None:
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(_encoded(payload))
        handle.flush()
        os.fsync(handle.fileno())


def _git(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _source_revision() -> str:
    return _git("rev-parse", "HEAD")


def _require_clean_claim_sources() -> None:
    tracked = set(_git("ls-files", "--", *B2_CLAIM_PATHS).splitlines())
    if tracked != set(B2_CLAIM_PATHS):
        raise ValueError("registered B2 claim source path set is not fully tracked")
    dirty = _git(
        "status", "--porcelain=v1", "--untracked-files=all", "--", *B2_CLAIM_PATHS
    )
    if dirty:
        raise ValueError(f"registered B2 claim sources differ from HEAD: {dirty}")


def _require_root(path: Path) -> Path:
    root = path.resolve()
    if ROOT_MARKER not in str(root).lower():
        raise ValueError(f"run root must contain assignment marker {ROOT_MARKER!r}")
    return root


def _require_bound_manifest(manifest: object) -> Mapping[str, object]:
    if not isinstance(manifest, Mapping):
        raise ValueError("manifest is not an object")
    issues = validate_manifest(manifest)
    if issues:
        raise ValueError("; ".join(issues))
    actual = _source_revision()
    if manifest.get("source_revision") != actual:
        raise ValueError(
            f"manifest source_revision {manifest.get('source_revision')!r} != HEAD {actual}"
        )
    return manifest


def _manifest_command(args: argparse.Namespace) -> int:
    actual = _source_revision()
    if args.source_revision != actual:
        raise ValueError(f"source_revision {args.source_revision!r} != HEAD {actual}")
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


def _technical_proof_command(args: argparse.Namespace) -> int:
    root = _require_root(args.run_root)
    manifest = _require_bound_manifest(_read_json(args.manifest))
    if manifest.get("technical_only") is not True:
        raise ValueError("technical-proof requires technical_only=true")
    proof_path = root / PROOF_NAME
    if proof_path.exists():
        raise FileExistsError("technical proof is already materialized")
    proof = preflight_report(manifest)
    _write_once(proof_path, proof)
    print(
        json.dumps(
            {
                "status": "VALID" if proof["all_passed"] else "INVALID",
                "result_bearing_runs": 0,
                "proof": str(proof_path),
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
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
    claim_path, result_path = root / CLAIM_NAME, root / RESULT_NAME
    if claim_path.exists() or result_path.exists():
        raise FileExistsError("the sole registered B2 full is already claimed")
    _exclusive_claim(
        claim_path,
        {
            "artifact_kind": "vsp02_b2_registered_full_claim",
            "assignment_id": B2_ASSIGNMENT_ID,
            "candidate": B2_CANDIDATE,
            "resource_class": B2_RESOURCE_CLASS,
            "pool_units": B2_POOL_UNITS,
            "run_id": manifest["run_id"],
            "source_revision": manifest["source_revision"],
            "manifest_identity": manifest_identity(manifest),
            "canonical_result_name": RESULT_NAME,
            "result_bearing_runs": 1,
            "retry_rescue_sweep": 0,
        },
    )
    # The unique invocation is consumed after the exclusive claim.  There is
    # no phase retry, rescue, sweep, or corrected second invocation.
    result = run_treatment(manifest, repo_root=PROJECT_ROOT)
    issues = validate_result(manifest, result, repo_root=PROJECT_ROOT)
    if issues:
        raise ValueError("result validation failed: " + "; ".join(issues))
    _write_once(result_path, result)
    return 0


def _validate_command(args: argparse.Namespace) -> int:
    root = _require_root(args.run_root)
    manifest = _read_json(root / MANIFEST_NAME)
    result = _read_json(root / RESULT_NAME)
    issues = validate_result(manifest, result, repo_root=PROJECT_ROOT)
    print(
        json.dumps(
            {"status": "VALID" if not issues else "INVALID", "issues": issues},
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0 if not issues else 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="VSP02-B2 paired shadow-learner localization"
    )
    commands = parser.add_subparsers(dest="command", required=True)

    manifest = commands.add_parser("manifest", help="write one immutable manifest")
    manifest.add_argument("--source-revision", required=True)
    manifest.add_argument("--run-id", required=True)
    manifest.add_argument("--technical-only", action="store_true")
    manifest.add_argument("--output", type=Path, required=True)
    manifest.set_defaults(handler=_manifest_command)

    proof = commands.add_parser(
        "technical-proof", help="run zero-episode P0-P8 construction proofs"
    )
    proof.add_argument("--manifest", type=Path, required=True)
    proof.add_argument("--run-root", type=Path, required=True)
    proof.set_defaults(handler=_technical_proof_command)

    full = commands.add_parser(
        "registered-full", help="consume the sole registered train/evaluate/analyze full"
    )
    full.add_argument("--manifest", type=Path, required=True)
    full.add_argument("--run-root", type=Path, required=True)
    full.set_defaults(handler=_registered_full_command)

    validate = commands.add_parser("validate", help="validate the retained full result")
    validate.add_argument("--run-root", type=Path, required=True)
    validate.set_defaults(handler=_validate_command)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    return arguments.handler(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
