"""Write-once runner for the frozen VSP02-B4 registered full."""

from __future__ import annotations

import argparse
import hashlib
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

from experiments.candidates.vsp_02.self_generated_closed_loop_feedback import (
    B4_ASSIGNMENT_ID,
    B4_CANDIDATE,
    B4_DEPENDENCY_PATHS,
    B4_POOL_UNITS,
    B4_RESOURCE_CLASS,
    B4_RUN_ID,
    B4_RUNTIME_PATHS,
    build_manifest,
    json_ready,
    manifest_identity,
    preflight_report,
    run_treatment,
    validate_manifest,
    validate_result,
)


FROZEN_HANDOFF_PATH = Path(
    r"C:\Projects\HMASD\temp\handoffs\explorer_to_code_manager"
    r"\2026-08-11_vsp02_b4_self_generated_closed_loop_feedback.md"
)
FROZEN_HANDOFF_SHA256 = "bd9aac55ec4f8aaa8adb88f8d20f3dc2fb2f45e7a0e17d01d7ef23caf63ac245"
FROZEN_PUBLICATION_COMMIT = "de5f2427662de2dc28fe20793086c0763d725018"
CANONICAL_RUN_ROOT = (
    PROJECT_ROOT / "temp" / "sessions" / "code_project_manager" / "vsp02_b4_self_generated_closed_loop_feedback"
).resolve()
MANIFEST_NAME = "frozen_manifest.json"
CLAIM_NAME = "registered_full_claim.json"
PROOF_NAME = "technical_proof.json"
RESULT_NAME = "raw_result.json"


def _read_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _encoded(payload: object) -> bytes:
    return json.dumps(json_ready(payload), ensure_ascii=True, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def _write_once(path: Path, payload: object) -> None:
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(f"refusing to overwrite write-once artifact: {target}")
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="xb", dir=target.parent, prefix=f".{target.name}.", delete=False) as handle:
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
    return subprocess.run(["git", *arguments], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True).stdout.strip()


def _source_revision() -> str:
    return _git("rev-parse", "HEAD")


def _require_frozen_handoff() -> None:
    if not FROZEN_HANDOFF_PATH.is_file():
        raise FileNotFoundError(f"frozen B4 handoff is unavailable: {FROZEN_HANDOFF_PATH}")
    actual = hashlib.sha256(FROZEN_HANDOFF_PATH.read_bytes()).hexdigest()
    if actual != FROZEN_HANDOFF_SHA256:
        raise ValueError(f"frozen B4 handoff digest {actual} != {FROZEN_HANDOFF_SHA256}")


def _require_publication_ancestry() -> None:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", FROZEN_PUBLICATION_COMMIT, "HEAD"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise ValueError(
            f"frozen publication commit {FROZEN_PUBLICATION_COMMIT} is not an ancestor of source HEAD"
        )


def _require_clean_claim_sources() -> None:
    tracked = set(_git("ls-files", "--", *B4_RUNTIME_PATHS).splitlines())
    if tracked != set(B4_RUNTIME_PATHS):
        raise ValueError("registered B4 claim and runtime dependency path set is not fully tracked")
    dirty = _git("status", "--porcelain=v1", "--untracked-files=all", "--", *B4_RUNTIME_PATHS)
    if dirty:
        raise ValueError(f"registered B4 claim or runtime dependency sources differ from HEAD: {dirty}")


def _require_root(path: Path) -> Path:
    root = path.resolve()
    if root != CANONICAL_RUN_ROOT:
        raise ValueError(f"run root must equal canonical assignment root {CANONICAL_RUN_ROOT}")
    return root


def _require_bound_manifest(manifest: object) -> Mapping[str, object]:
    if not isinstance(manifest, Mapping):
        raise ValueError("manifest is not an object")
    issues = validate_manifest(manifest)
    if issues:
        raise ValueError("; ".join(issues))
    actual = _source_revision()
    if manifest.get("source_revision") != actual:
        raise ValueError(f"manifest source_revision {manifest.get('source_revision')!r} != HEAD {actual}")
    return manifest


def _manifest_command(args: argparse.Namespace) -> int:
    _require_frozen_handoff()
    actual = _source_revision()
    if args.source_revision != actual:
        raise ValueError(f"source_revision {args.source_revision!r} != HEAD {actual}")
    manifest = build_manifest(source_revision=actual, run_id=args.run_id, technical_only=args.technical_only)
    issues = validate_manifest(manifest)
    if issues:
        raise ValueError("; ".join(issues))
    _write_once(args.output, manifest)
    return 0


def _technical_proof_command(args: argparse.Namespace) -> int:
    _require_frozen_handoff()
    root = _require_root(args.run_root)
    manifest = _require_bound_manifest(_read_json(args.manifest))
    if manifest.get("technical_only") is not True:
        raise ValueError("technical-proof requires technical_only=true")
    proof = preflight_report(manifest, repo_root=PROJECT_ROOT)
    _write_once(root / PROOF_NAME, proof)
    print(json.dumps({"status": "VALID" if proof["all_passed"] else "INVALID", "result_bearing_runs": 0, "proof": str(root / PROOF_NAME)}, separators=(",", ":"), sort_keys=True))
    return 0 if proof["all_passed"] else 2


def _registered_full_command(args: argparse.Namespace) -> int:
    _require_frozen_handoff()
    root = _require_root(args.run_root)
    if Path.cwd().resolve() != PROJECT_ROOT:
        raise ValueError(f"registered-full cwd must be bound source worktree {PROJECT_ROOT}")
    manifest_path = (root / MANIFEST_NAME).resolve()
    if args.manifest.resolve() != manifest_path:
        raise ValueError(f"registered-full manifest must be {manifest_path}")
    manifest = _require_bound_manifest(_read_json(manifest_path))
    if manifest.get("technical_only") is not False or manifest.get("run_id") != B4_RUN_ID:
        raise ValueError(f"registered-full requires technical_only=false and run_id={B4_RUN_ID}")
    _require_clean_claim_sources()
    _require_publication_ancestry()
    preflight = preflight_report(manifest, repo_root=PROJECT_ROOT)
    if not isinstance(preflight, Mapping) or preflight.get("all_passed") is not True:
        raise ValueError("registered-full preflight failed before sole claim creation")
    claim_path, result_path = root / CLAIM_NAME, root / RESULT_NAME
    if claim_path.exists() or result_path.exists():
        raise FileExistsError("the sole registered B4 full is already claimed")
    _exclusive_claim(claim_path, {
        "artifact_kind": "vsp02_b4_registered_full_claim",
        "assignment_id": B4_ASSIGNMENT_ID,
        "candidate": B4_CANDIDATE,
        "resource_class": B4_RESOURCE_CLASS,
        "pool_units": B4_POOL_UNITS,
        "run_id": manifest["run_id"],
        "source_revision": manifest["source_revision"],
        "manifest_identity": manifest_identity(manifest),
        "frozen_handoff": {"path": str(FROZEN_HANDOFF_PATH), "sha256": FROZEN_HANDOFF_SHA256, "publication_commit": FROZEN_PUBLICATION_COMMIT},
        "canonical_result_name": RESULT_NAME,
        "result_bearing_runs": 1,
        "retry_rescue_sweep_extra_arm_seed_checkpoint": 0,
    })
    # Claim creation consumes the one invocation; this path intentionally has no retry or rescue.
    result = run_treatment(manifest, repo_root=PROJECT_ROOT)
    issues = validate_result(manifest, result, repo_root=PROJECT_ROOT)
    if issues:
        raise ValueError("result validation failed: " + "; ".join(issues))
    _write_once(result_path, result)
    return 0


def _validate_command(args: argparse.Namespace) -> int:
    _require_frozen_handoff()
    root = _require_root(args.run_root)
    manifest, result = _read_json(root / MANIFEST_NAME), _read_json(root / RESULT_NAME)
    issues = validate_result(manifest, result, repo_root=PROJECT_ROOT)
    print(json.dumps({"status": "VALID" if not issues else "INVALID", "issues": issues}, separators=(",", ":"), sort_keys=True))
    return 0 if not issues else 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VSP02-B4 self-generated closed-loop feedback")
    commands = parser.add_subparsers(dest="command", required=True)
    manifest = commands.add_parser("manifest")
    manifest.add_argument("--source-revision", required=True)
    manifest.add_argument("--run-id", required=True)
    manifest.add_argument("--technical-only", action="store_true")
    manifest.add_argument("--output", type=Path, required=True)
    manifest.set_defaults(handler=_manifest_command)
    proof = commands.add_parser("technical-proof")
    proof.add_argument("--manifest", type=Path, required=True)
    proof.add_argument("--run-root", type=Path, required=True)
    proof.set_defaults(handler=_technical_proof_command)
    full = commands.add_parser("registered-full")
    full.add_argument("--manifest", type=Path, required=True)
    full.add_argument("--run-root", type=Path, required=True)
    full.set_defaults(handler=_registered_full_command)
    validate = commands.add_parser("validate")
    validate.add_argument("--run-root", type=Path, required=True)
    validate.set_defaults(handler=_validate_command)
    return parser


def main() -> int:
    args = _parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
