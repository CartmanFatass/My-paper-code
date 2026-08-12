"""Source-bound write-once runner for the frozen VSP02-B5 registered full."""

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

from experiments.candidates.vsp_02.vsp02_b5_full_adam_state_continuity import (
    B5_ASSIGNMENT_ID, B5_CANDIDATE, B5_POOL_UNITS, B5_RESOURCE_CLASS, B5_RUN_ID,
    B5_RUNTIME_PATHS, B5_FREEZE_PUBLICATION_COMMIT, build_manifest, classify_b5,
    analyze_registered_full, digest, evaluate_registered_full, json_ready,
    manifest_identity, preflight_report, run_treatment,
    validate_manifest, validate_preflight_evidence, validate_result,
)


FROZEN_HANDOFF_PATH = Path(r"C:\Projects\HMASD\temp\handoffs\explorer_to_code_manager\2026-08-11_vsp02_b5_full_adam_state_continuity_loop_04_final_implementation.md")
FROZEN_HANDOFF_SHA256 = "72ac01d9dfb7aaf9b7f6d73cddc084c128bfded5e731d59147445a45e1672018"
CANONICAL_RUN_ROOT = (PROJECT_ROOT / "temp" / "sessions" / "code_project_manager" / "vsp02_b5_full_adam_state_continuity").resolve()
MANIFEST_NAME = "frozen_manifest.json"
CLAIM_NAME = "registered_full_claim.json"
RESULT_NAME = "raw_result.json"
READINESS_NAME = "readiness_zero_runtime.json"
READINESS_BOUNDED_NAME = "readiness_bounded_exercise.json"


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
        raise FileNotFoundError(f"frozen B5 handoff unavailable: {FROZEN_HANDOFF_PATH}")
    actual = hashlib.sha256(FROZEN_HANDOFF_PATH.read_bytes()).hexdigest()
    if actual != FROZEN_HANDOFF_SHA256:
        raise ValueError(f"frozen B5 handoff digest {actual} != {FROZEN_HANDOFF_SHA256}")


def _require_publication_ancestry() -> None:
    if subprocess.run(["git", "merge-base", "--is-ancestor", B5_FREEZE_PUBLICATION_COMMIT, "HEAD"], cwd=PROJECT_ROOT).returncode != 0:
        raise ValueError(f"frozen publication {B5_FREEZE_PUBLICATION_COMMIT} is not an ancestor of HEAD")


def _require_clean_claim_sources() -> None:
    tracked = set(_git("ls-files", "--", *B5_RUNTIME_PATHS).splitlines())
    if tracked != set(B5_RUNTIME_PATHS):
        raise ValueError("registered B5 claim and dependency paths are not fully tracked")
    dirty = _git("status", "--porcelain=v1", "--untracked-files=all", "--", *B5_RUNTIME_PATHS)
    if dirty:
        raise ValueError(f"registered B5 claim or dependency sources differ from HEAD: {dirty}")


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


def _readiness_payload(phase: str, *, source_revision: str) -> dict[str, object]:
    meanings = {
        "interface_smoke": "import and CLI surface only",
        "bounded_exercise": "retained zero-activity contract fixture only",
        "artifact_validation": "pure retained fixture validation",
        "artifact_reload": "byte/digest-stable retained fixture reload",
        "evaluate_entry": "evaluation entry is full-only; no evaluation",
        "analyze_entry": "analysis entry is full-only; classifier total; no analysis",
    }
    payload = {"artifact_kind": "vsp02_b5_zero_runtime_readiness", "assignment_id": B5_ASSIGNMENT_ID,
               "phase": phase, "meaning": meanings[phase], "source_revision": source_revision,
               "formal": False, "scientific_iteration_cost": 0,
               "activity": {"result_bearing_runs": 0, "real_training_episodes": 0, "evaluation_episodes": 0,
                            "environment_transitions": 0, "optimizer_updates": 0, "checkpoints_total": 0,
                            "retries_rescues_sweeps": 0}}
    payload["evidence_digest"] = digest(payload)
    return payload


def _require_bounded_readiness(root: Path, *, source_revision: str, reload_twice: bool) -> Mapping[str, object]:
    """Validate/reload the retained bounded-exercise artifact without runtime."""

    path = root / READINESS_BOUNDED_NAME
    first_bytes = path.read_bytes()
    retained = _read_json(path)
    if not isinstance(retained, Mapping):
        raise ValueError("bounded readiness artifact is not an object")
    unsigned = dict(retained)
    evidence = unsigned.pop("evidence_digest", None)
    expected_activity = _readiness_payload("bounded_exercise", source_revision=source_revision)["activity"]
    if (
        retained.get("artifact_kind") != "vsp02_b5_zero_runtime_readiness"
        or retained.get("assignment_id") != B5_ASSIGNMENT_ID
        or retained.get("phase") != "bounded_exercise"
        or retained.get("source_revision") != source_revision
        or retained.get("formal") is not False
        or retained.get("scientific_iteration_cost") != 0
        or retained.get("activity") != expected_activity
        or evidence != digest(unsigned)
    ):
        raise ValueError("bounded readiness phase/source/digest or zero-activity contract mismatch")
    if reload_twice and path.read_bytes() != first_bytes:
        raise ValueError("bounded readiness reload changed retained bytes")
    return retained


def _expect_full_only_rejection(call: object, *, expected: str) -> str:
    if not callable(call):
        raise TypeError("full-only entry probe must be callable")
    try:
        call()
    except ValueError as error:
        observed = str(error)
        if observed != expected:
            raise AssertionError(f"unexpected full-only rejection: {observed}") from error
        return observed
    raise AssertionError("technical-only readiness input reached a full runtime entry")


def _readiness_command(args: argparse.Namespace) -> int:
    _require_frozen_handoff()
    root = _require_root(args.run_root)
    phase = args.command.replace("readiness-", "").replace("-", "_")
    source_revision = _source_revision()
    observation: dict[str, object] = {}
    if phase == "interface_smoke":
        _write_once(root / READINESS_NAME, _readiness_payload(phase, source_revision=source_revision))
    elif phase == "bounded_exercise":
        # A fresh successor retains the bounded phase without mutating interface smoke.
        _write_once(root / READINESS_BOUNDED_NAME, _readiness_payload(phase, source_revision=source_revision))
    elif phase == "artifact_validation":
        retained = _require_bounded_readiness(root, source_revision=source_revision, reload_twice=False)
        observation = {"validated_artifact": READINESS_BOUNDED_NAME,
                       "validated_phase": retained["phase"], "validated_source_revision": retained["source_revision"],
                       "validated_evidence_digest": retained["evidence_digest"]}
    elif phase == "artifact_reload":
        retained = _require_bounded_readiness(root, source_revision=source_revision, reload_twice=True)
        observation = {"reloaded_artifact": READINESS_BOUNDED_NAME,
                       "reloaded_phase": retained["phase"], "reloaded_source_revision": retained["source_revision"],
                       "reloaded_evidence_digest": retained["evidence_digest"], "byte_stable": True}
    elif phase == "evaluate_entry":
        technical = build_manifest(source_revision=source_revision, run_id="B5-READINESS", technical_only=True)
        rejection = _expect_full_only_rejection(
            lambda: evaluate_registered_full(technical, {"phase": "train", "units": []}),
            expected="evaluate is full-only and requires the in-process registered train phase",
        )
        observation = {"entry_called": "evaluate_registered_full", "technical_only": True,
                       "expected_full_only_rejection": rejection, "evaluation_activity": 0}
    elif phase == "analyze_entry":
        technical = build_manifest(source_revision=source_revision, run_id="B5-READINESS", technical_only=True)
        rejection = _expect_full_only_rejection(
            lambda: analyze_registered_full(
                technical, {}, {"phase": "train"}, {"phase": "evaluate"},
                {"all_resource_caps_passed": True},
            ),
            expected="analyze is full-only and requires ordered train then evaluate phases",
        )
        observed = {classify_b5(valid=False, carry_success=set(), reset_success=set())}
        panels = [set(), {"U1"}, {"U2"}, {"U1", "U2"}]
        observed.update(classify_b5(valid=True, carry_success=carry, reset_success=reset) for carry in panels for reset in panels)
        if observed != set(technical["branches"]):
            raise AssertionError("six-branch classifier is not total")
        observation = {"entry_called": "analyze_registered_full", "technical_only": True,
                       "expected_full_only_rejection": rejection, "analysis_activity": 0,
                       "classifier_branches_observed": sorted(observed), "classifier_total": True}
    print(json.dumps({"status": "VALID", "phase": phase, "result_bearing_runs": 0,
                      "observation": observation}, separators=(",", ":"), sort_keys=True))
    return 0


def _registered_full_command(args: argparse.Namespace) -> int:
    _require_frozen_handoff()
    root = _require_root(args.run_root)
    if Path.cwd().resolve() != PROJECT_ROOT:
        raise ValueError(f"registered-full cwd must be source worktree {PROJECT_ROOT}")
    manifest_path = (root / MANIFEST_NAME).resolve()
    if args.manifest.resolve() != manifest_path:
        raise ValueError(f"registered-full manifest must be {manifest_path}")
    manifest = _require_bound_manifest(_read_json(manifest_path))
    if manifest.get("technical_only") is not False or manifest.get("run_id") != B5_RUN_ID:
        raise ValueError(f"registered-full requires technical_only=false and run_id={B5_RUN_ID}")
    _require_clean_claim_sources()
    _require_publication_ancestry()
    preflight = preflight_report(manifest, repo_root=PROJECT_ROOT)
    if preflight.get("all_passed") is not True:
        raise ValueError("registered-full preflight failed before sole claim creation")
    claim_path, result_path = root / CLAIM_NAME, root / RESULT_NAME
    if claim_path.exists() or result_path.exists():
        raise FileExistsError("the sole registered B5 full is already claimed")
    _exclusive_claim(claim_path, {
        "artifact_kind": "vsp02_b5_registered_full_claim", "assignment_id": B5_ASSIGNMENT_ID,
        "candidate": B5_CANDIDATE, "resource_class": B5_RESOURCE_CLASS, "pool_units": B5_POOL_UNITS,
        "run_id": manifest["run_id"], "source_revision": manifest["source_revision"],
        "manifest_identity": manifest_identity(manifest),
        "frozen_handoff": {"path": str(FROZEN_HANDOFF_PATH), "sha256": FROZEN_HANDOFF_SHA256,
                           "publication_commit": B5_FREEZE_PUBLICATION_COMMIT},
        "ordered_lifecycle": ["train", "evaluate", "analyze"], "canonical_result_name": RESULT_NAME,
        "result_bearing_runs": 1, "retry_rescue_sweep_extra_root_checkpoint_threshold_boundary": 0,
    })
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
    parser = argparse.ArgumentParser(description="VSP02-B5 full Adam state continuity")
    commands = parser.add_subparsers(dest="command", required=True)
    manifest = commands.add_parser("manifest")
    manifest.add_argument("--source-revision", required=True); manifest.add_argument("--run-id", required=True)
    manifest.add_argument("--technical-only", action="store_true"); manifest.add_argument("--output", type=Path, required=True)
    manifest.set_defaults(handler=_manifest_command)
    for name in ("readiness-interface-smoke", "readiness-bounded-exercise", "readiness-artifact-validation",
                 "readiness-artifact-reload", "readiness-evaluate-entry", "readiness-analyze-entry"):
        command = commands.add_parser(name); command.add_argument("--run-root", type=Path, required=True)
        command.set_defaults(handler=_readiness_command)
    full = commands.add_parser("registered-full")
    full.add_argument("--manifest", type=Path, required=True); full.add_argument("--run-root", type=Path, required=True)
    full.set_defaults(handler=_registered_full_command)
    validate = commands.add_parser("validate"); validate.add_argument("--run-root", type=Path, required=True)
    validate.set_defaults(handler=_validate_command)
    return parser


def main() -> int:
    args = _parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
