"""Fail-closed prelaunch validation for the complete R03 transaction."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

from .production_contract import (
    DIRECTION_GIT_PATHS,
    OUTPUT_ROOT,
    PAYLOAD_MODULE,
    RUN_ID,
    canonical_json_bytes,
    conservative_estimate_document,
    document_sha256,
    parameters_document,
    payload_argv,
)
from .production_manifest import build_checkpoint_manifest_contract


class PrelaunchRefusal(PermissionError):
    pass


def read_json(path: Path) -> Mapping[str, object]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PrelaunchRefusal("immutable JSON is absent or malformed") from exc
    if not isinstance(value, Mapping):
        raise PrelaunchRefusal("immutable JSON must be an object")
    return value


def read_canonical_json(path: Path) -> Mapping[str, object]:
    """Require exactly the canonical bytes emitted by production_manifest."""

    target = Path(path)
    try:
        payload = target.read_bytes()
        if payload.startswith(b"\xef\xbb\xbf"):
            raise PrelaunchRefusal("canonical JSON must not contain a BOM")
        value = json.loads(payload.decode("utf-8"))
    except PrelaunchRefusal:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PrelaunchRefusal("canonical JSON is absent or malformed") from exc
    if not isinstance(value, Mapping) or canonical_json_bytes(value) != payload:
        raise PrelaunchRefusal("JSON bytes are not one canonical strict value")
    return value


def _require_sha(value: object, label: str, lengths: tuple[int, ...] = (64,)) -> str:
    if not isinstance(value, str) or len(value) not in lengths:
        raise PrelaunchRefusal(f"{label} hash is missing")
    try:
        bytes.fromhex(value)
    except ValueError as exc:
        raise PrelaunchRefusal(f"{label} hash is missing") from exc
    return value.lower()


def validate_exact_documents(
    parameters: Mapping[str, object], estimate: Mapping[str, object]
) -> None:
    if dict(parameters) != parameters_document():
        raise PrelaunchRefusal("parameter override is forbidden")
    if dict(estimate) != conservative_estimate_document():
        raise PrelaunchRefusal("resource estimate override is forbidden")


def validate_output_precondition(repository_root: Path, output_root: str = OUTPUT_ROOT) -> str:
    if output_root != OUTPUT_ROOT:
        raise PrelaunchRefusal("output-root override is forbidden")
    root = Path(repository_root).resolve()
    destination = (root / Path(*output_root.split("/"))).resolve(strict=False)
    try:
        destination.relative_to(root)
    except ValueError as exc:
        raise PrelaunchRefusal("output root escapes repository") from exc
    if destination.exists():
        if not destination.is_dir() or destination.is_symlink() or any(destination.iterdir()):
            raise PrelaunchRefusal("nonempty destination is forbidden")
        return "EMPTY"
    return "ABSENT"


def validate_source_manifest(repository_root: Path, manifest: Mapping[str, object]) -> None:
    rows = manifest.get("files")
    if manifest.get("complete") is not True or not isinstance(rows, list) or not rows:
        raise PrelaunchRefusal("source manifest is incomplete")
    root = Path(repository_root).resolve()
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise PrelaunchRefusal("source manifest row is malformed")
        relative = row.get("path")
        expected = _require_sha(row.get("sha256"), "source")
        if not isinstance(relative, str) or relative in seen or "\\" in relative or ".." in relative.split("/"):
            raise PrelaunchRefusal("source path is invalid or duplicated")
        seen.add(relative)
        path = (root / Path(*relative.split("/"))).resolve(strict=True)
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise PrelaunchRefusal("source path escapes repository") from exc
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise PrelaunchRefusal("source hash differs")
    if seen != set(DIRECTION_GIT_PATHS):
        raise PrelaunchRefusal("source manifest path set differs")


def validate_checkpoint_manifest_contract(manifest: Mapping[str, object]) -> None:
    if dict(manifest) != build_checkpoint_manifest_contract():
        raise PrelaunchRefusal("checkpoint manifest contract differs or lacks hashes")


def validate_prelaunch_manifest(
    manifest: Mapping[str, object],
    *,
    source_manifest: Mapping[str, object],
    release_required: bool,
) -> None:
    if manifest.get("run_id") != RUN_ID:
        raise PrelaunchRefusal("run-id override is forbidden")
    if manifest.get("payload_argv") != list(payload_argv()):
        raise PrelaunchRefusal("payload argv differs")
    if manifest.get("parameters_sha256") != document_sha256(parameters_document()):
        raise PrelaunchRefusal("parameter hash differs")
    if manifest.get("estimate_sha256") != document_sha256(conservative_estimate_document()):
        raise PrelaunchRefusal("estimate hash differs")
    if manifest.get("source_manifest_sha256") != document_sha256(source_manifest):
        raise PrelaunchRefusal("source-manifest hash differs")
    if manifest.get("checkpoint_manifest_sha256") != document_sha256(build_checkpoint_manifest_contract()):
        raise PrelaunchRefusal("checkpoint-manifest hash differs")
    if manifest.get("rerun_permitted") is not False or manifest.get("effect_refs") != []:
        raise PrelaunchRefusal("rerun/effect contract differs")
    if (
        manifest.get("output_effect")
        != {
            "kind": "DIRECTORY_CREATE_ONLY",
            "resource_id": OUTPUT_ROOT,
            "operation": "create_and_populate_once",
        }
        or manifest.get("output_precondition") != "ABSENT_OR_EMPTY_BEFORE_PREPARE"
        or manifest.get("publication") != "ONE_ATOMIC_COMPLETE_PACKAGE_ONLY"
        or manifest.get("operator_now") is not False
    ):
        raise PrelaunchRefusal("output/publication firewall differs")
    git = manifest.get("git")
    if not isinstance(git, Mapping):
        raise PrelaunchRefusal("Git/code-SHA prerequisites are missing")
    if (
        git.get("required_branch_prefix") != "omp/ucope/"
        or git.get("required_clean_candidate_head") is not True
        or git.get("direction_owned_paths") != list(DIRECTION_GIT_PATHS)
        or git.get("prepare_code_sha_must_equal_head") is not True
    ):
        raise PrelaunchRefusal("Git/code-SHA prerequisites differ")
    code_sha = _require_sha(git.get("required_code_sha"), "code", (40,)) if release_required else git.get("required_code_sha")
    branch = git.get("observed_branch")
    if release_required and (
        not isinstance(branch, str)
        or not branch.startswith("omp/ucope/")
        or not code_sha
        or manifest.get("empirical_activity_released") is not True
    ):
        raise PrelaunchRefusal("later launch release is absent")
    if not release_required and manifest.get("empirical_activity_released") is not False:
        raise PrelaunchRefusal("S3 cannot release empirical activity")


def validate_live_hmasd_manifest(
    manifest: Mapping[str, object], *, code_sha: str
) -> None:
    """Validate the later hmasd_run-owned manifest without creating it."""

    expected_code = _require_sha(code_sha, "code", (40,))
    command = manifest.get("command")
    estimate = conservative_estimate_document()
    expected_hmasd_estimate = {
        "wall_seconds": estimate["wall_seconds"],
        "basis": estimate["basis"],
        "peak_memory_gib": estimate["peak_memory_gib"],
    }
    if (
        manifest.get("run_id") != RUN_ID
        or manifest.get("direction_id") != "ucope"
        or manifest.get("code_sha") != expected_code
        or command != list(payload_argv())
        or manifest.get("status") != "RUNNING"
        or manifest.get("parameters") != parameters_document()
        or manifest.get("estimate") != expected_hmasd_estimate
    ):
        raise PrelaunchRefusal("hmasd_run manifest does not byte-bind the frozen launch")
    if not isinstance(command, Sequence) or PAYLOAD_MODULE not in command:
        raise PrelaunchRefusal("renamed payload module is absent")


FORBIDDEN_OPTIONS = frozenset(
    {
        "--seed", "--master-seed", "--arm", "--panel", "--diagnostic",
        "--skip-diagnostic", "--partial", "--result", "--query", "--rerun",
    }
)


def reject_forbidden_options(argv: Sequence[str]) -> None:
    for token in argv:
        option = token.split("=", 1)[0]
        if option in FORBIDDEN_OPTIONS:
            raise PrelaunchRefusal("responsive or partial override is forbidden")
