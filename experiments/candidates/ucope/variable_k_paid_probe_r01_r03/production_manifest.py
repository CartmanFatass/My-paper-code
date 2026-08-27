"""Hash-bound manifests for the prospective UCOPE R03 empirical transaction."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Mapping, Sequence

from .production_contract import (
    DEFAULT_RUN_BINDING,
    DIRECTION_GIT_PATHS,
    RunBinding,
    checkpoint_slots,
    canonical_json_bytes,
    conservative_estimate_document,
    document_sha256,
    parameters_document,
    payload_argv,
    repo_path,
    require_canonical_run_binding,
)


class ManifestError(ValueError):
    pass


S3_ARTIFACT_NAMES = (
    "S3_PARAMETERS.json",
    "S3_CONSERVATIVE_ESTIMATE.json",
    "S3_SOURCE_MANIFEST.json",
    "S3_CHECKPOINT_MANIFEST_CONTRACT.json",
    "S3_PRELAUNCH_MANIFEST.json",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_source_run_binding(
    source_manifest: Mapping[str, object], binding: RunBinding
) -> None:
    observed = source_manifest.get("run_binding")
    if binding == DEFAULT_RUN_BINDING:
        if "run_binding" in source_manifest:
            raise ManifestError("source manifest is bound to another run")
    elif observed != binding.reference_document():
        raise ManifestError("source manifest run/authority binding differs")


def write_canonical_json_atomic(path: Path, value: Mapping[str, object]) -> dict[str, str]:
    """Replace one artifact with exactly one canonical strict UTF-8 JSON value."""

    target = Path(path)
    if not target.parent.is_dir() or target.parent.is_symlink() or target.is_symlink():
        raise ManifestError("canonical artifact path is absent, aliased, or not a directory")
    payload = canonical_json_bytes(value)
    # Validate the rendered bytes before they can replace current evidence.
    try:
        parsed = json.loads(payload.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ManifestError("canonical artifact renderer produced invalid JSON") from exc
    if not isinstance(parsed, Mapping) or canonical_json_bytes(parsed) != payload:
        raise ManifestError("canonical artifact renderer is not byte-stable")
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = stream.name
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
    observed = target.read_bytes()
    if observed != payload:
        raise ManifestError("canonical artifact bytes differ after atomic replace")
    return {"path": target.as_posix(), "sha256": hashlib.sha256(observed).hexdigest()}


def emit_prelaunch_artifacts(
    repository_root: Path,
    artifact_directory: Path,
    *,
    observed_branch: str,
    code_sha: str | None,
    binding: RunBinding = DEFAULT_RUN_BINDING,
) -> dict[str, dict[str, str]]:
    """Atomically regenerate the five cross-bound S3 prelaunch artifacts."""

    binding = require_canonical_run_binding(binding)
    root = Path(repository_root).resolve()
    destination = Path(artifact_directory).resolve()
    try:
        destination.relative_to(root)
    except ValueError as exc:
        raise ManifestError("prelaunch artifact directory escapes repository") from exc
    source = build_source_manifest(root, binding=binding)
    documents: tuple[tuple[str, Mapping[str, object]], ...] = (
        ("S3_PARAMETERS.json", parameters_document(binding)),
        ("S3_CONSERVATIVE_ESTIMATE.json", conservative_estimate_document(binding)),
        ("S3_SOURCE_MANIFEST.json", source),
        (
            "S3_CHECKPOINT_MANIFEST_CONTRACT.json",
            build_checkpoint_manifest_contract(binding),
        ),
        (
            "S3_PRELAUNCH_MANIFEST.json",
            build_prelaunch_manifest(
                source_manifest=source,
                code_sha=code_sha,
                branch=observed_branch,
                empirical_activity_released=False,
                binding=binding,
            ),
        ),
    )
    refs: dict[str, dict[str, str]] = {}
    for name, document in documents:
        ref = write_canonical_json_atomic(destination / name, document)
        ref["path"] = (destination / name).relative_to(root).as_posix()
        refs[name] = ref
    if tuple(refs) != S3_ARTIFACT_NAMES:
        raise ManifestError("prelaunch artifact roster differs")
    return refs


def build_source_manifest(
    repository_root: Path, binding: RunBinding = DEFAULT_RUN_BINDING
) -> dict[str, object]:
    binding = require_canonical_run_binding(binding)
    root = Path(repository_root).resolve()
    files: list[dict[str, str]] = []
    for relative in DIRECTION_GIT_PATHS:
        target = repo_path(root, relative)
        if not target.is_file() or target.is_symlink():
            raise ManifestError(f"required source/test path absent: {relative}")
        files.append({"path": relative, "sha256": _sha256(target)})
    document: dict[str, object] = {
        "schema": "UCOPE_R01_R03_EMPIRICAL_SOURCE_MANIFEST_V1",
        "complete": True,
        "files": files,
    }
    # The historical -01 bytes remain exact.  The replacement source reference
    # additionally binds the purchased identity and its authority.
    if binding != DEFAULT_RUN_BINDING:
        document["run_binding"] = binding.reference_document()
    return document


def build_checkpoint_manifest_contract(
    binding: RunBinding = DEFAULT_RUN_BINDING,
) -> dict[str, object]:
    """Describe the final inventory and its mandatory future content hashes."""

    require_canonical_run_binding(binding)
    return {
        "schema": "UCOPE_R01_R03_EMPIRICAL_CHECKPOINT_MANIFEST_CONTRACT_V1",
        "complete": True,
        "slot_count": 90,
        "slots": [
            {**slot, "sha256_required": True, "model_sha256_required": True}
            for slot in checkpoint_slots()
        ],
        "missing_hash_policy": "REFUSE",
        "cold_load_before_evaluation": True,
    }


def build_prelaunch_manifest(
    *,
    source_manifest: Mapping[str, object],
    code_sha: str | None,
    branch: str | None,
    empirical_activity_released: bool = False,
    binding: RunBinding = DEFAULT_RUN_BINDING,
) -> dict[str, object]:
    binding = require_canonical_run_binding(binding)
    _require_source_run_binding(source_manifest, binding)
    parameters = parameters_document(binding)
    estimate = conservative_estimate_document(binding)
    checkpoints = build_checkpoint_manifest_contract(binding)
    document: dict[str, object] = {
        "schema": "UCOPE_R01_R03_EMPIRICAL_PRELAUNCH_MANIFEST_V1",
        "run_id": binding.run_id,
        "parameters_location": "hmasd_run.manifest.parameters",
        "parameters_sha256": document_sha256(parameters),
        "estimate_location": "hmasd_run.manifest.estimate",
        "estimate_sha256": document_sha256(estimate),
        "source_manifest_path": binding.source_manifest_path,
        "source_manifest_sha256": document_sha256(source_manifest),
        "checkpoint_manifest_path": binding.checkpoint_manifest_path,
        "checkpoint_manifest_sha256": document_sha256(checkpoints),
        "hmasd_manifest_path": binding.hmasd_manifest_path,
        "prelaunch_manifest_path": binding.prelaunch_manifest_path,
        "payload_argv": list(payload_argv(binding)),
        "output_effect": binding.output_effect(),
        "output_precondition": "ABSENT_OR_EMPTY_BEFORE_PREPARE",
        "publication": "ONE_ATOMIC_COMPLETE_PACKAGE_ONLY",
        "rerun_permitted": False,
        "git": {
            "required_branch_prefix": "omp/ucope/",
            "required_clean_candidate_head": True,
            "required_code_sha": code_sha,
            "observed_branch": branch,
            "direction_owned_paths": list(DIRECTION_GIT_PATHS),
            "prepare_code_sha_must_equal_head": True,
        },
        "empirical_activity_released": empirical_activity_released,
        "operator_now": False,
        "effect_refs": [],
    }
    if binding != DEFAULT_RUN_BINDING:
        document["authority_refs"] = binding.authority_document()
    return document


def complete_checkpoint_manifest(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Normalize a future content-addressed inventory; no checkpoint is read."""

    expected = checkpoint_slots()
    if len(rows) != len(expected):
        raise ManifestError("checkpoint manifest requires exactly 90 rows")
    normalized: list[dict[str, object]] = []
    for observed, contract in zip(rows, expected, strict=True):
        identity = {key: observed.get(key) for key in contract}
        if identity != contract:
            raise ManifestError("checkpoint identity/order differs")
        for name in ("sha256", "model_sha256"):
            value = observed.get(name)
            if not isinstance(value, str) or len(value) != 64:
                raise ManifestError("checkpoint hashes are required")
            try:
                bytes.fromhex(value)
            except ValueError as exc:
                raise ManifestError("checkpoint hashes are required") from exc
        normalized.append(dict(observed))
    return {
        "schema": "UCOPE_R01_R03_EMPIRICAL_CHECKPOINT_MANIFEST_V1",
        "complete": True,
        "slot_count": 90,
        "slots": normalized,
    }
