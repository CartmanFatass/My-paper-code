"""Complete-only registered evaluation and value-free terminal evidence."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Mapping, Sequence

from .production_manifest import write_canonical_json_atomic
from .s2_construction import (
    BoundaryRequest,
    CheckpointSlot,
    evaluate_complete_private,
    publish_complete_package,
    read_atomic_sealed_blob,
)


REGISTERED_RESULT_NAMESPACE = "REGISTERED_UCOPE_R01_R03_COMPLETE_RESULT_V1"


def registered_result_request() -> BoundaryRequest:
    return BoundaryRequest(
        namespace=REGISTERED_RESULT_NAMESPACE,
        registered_master_seeds=True,
        complete_registered_panel=True,
        question_relevant_output=True,
        gpu=False,
    )


def build_value_free_evidence(
    *,
    run_id: str,
    code_sha: str,
    checkpoint_manifest_sha256: str,
    completion: Mapping[str, object],
    sealed_result_sha256: str,
) -> dict[str, object]:
    return {
        "schema": "UCOPE_R01_R03_COMPLETE_EVIDENCE_V1",
        "run_id": run_id,
        "code_sha": code_sha,
        "checkpoint_manifest_sha256": checkpoint_manifest_sha256,
        "completion_schema": completion["schema"],
        "completion_digest": completion["completeness_digest"],
        "package_sha256": completion["package_sha256"],
        "sealed_result_sha256": sealed_result_sha256,
        "complete_r03_package": True,
        "atomic_complete_only": True,
        "partial_result": False,
        "scientific_values_in_evidence": False,
        "rerun_permitted": False,
    }


def evaluate_publish_complete(
    checkpoint_paths: Sequence[Path],
    *,
    checkpoint_root: Path,
    output_root: Path,
    destination: Path,
    evidence_path: Path,
    checkpoint_manifest_sha256: str,
    run_id: str,
    code_sha: str,
) -> dict[str, object]:
    request = registered_result_request()
    evaluation = evaluate_complete_private(
        [CheckpointSlot(path) for path in checkpoint_paths],
        checkpoint_root=checkpoint_root,
        request=request,
    )
    completion = publish_complete_package(
        evaluation, destination=destination, output_root=output_root, request=request
    )
    sealed = read_atomic_sealed_blob(destination)
    evidence = build_value_free_evidence(
        run_id=run_id,
        code_sha=code_sha,
        checkpoint_manifest_sha256=checkpoint_manifest_sha256,
        completion=completion,
        sealed_result_sha256=hashlib.sha256(sealed).hexdigest(),
    )
    write_canonical_json_atomic(evidence_path, evidence)
    return evidence
