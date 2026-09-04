"""Canonical child-process entry for one admitted OMRC B1 arm-seed slice."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys
import tempfile
import traceback
from typing import Any, Mapping

from .artifact import canonical_json_bytes, ensure_confined
from .b1_contract import (
    B1ArmSeedRequest,
    B1Plan,
)
from .b1_engine import B1_RAW_EVIDENCE_SCHEMA, b1_engine
from .telemetry import ResourceCaps


WORKER_REQUEST_SCHEMA = "cbsc_omrc_b01_b1_worker_request_v1"
WORKER_RESULT_SCHEMA = "cbsc_omrc_b01_b1_worker_raw_result_v1"
WORKER_ERROR_SCHEMA = "cbsc_omrc_b01_b1_worker_error_v1"
_REQUEST_KEYS = frozenset(
    {
        "schema",
        "attempt_root",
        "attempt_id",
        "arm",
        "seed",
        "train_episode_ids",
        "checkpoint_updates",
        "eval_stochastic_ids",
        "eval_motif_ids",
        "scratch_root",
        "durable_root",
        "admission_schema",
        "admission_receipt_path",
        "admission_receipt_sha256",
        "implementation_commit",
        "source_conformance_sha256",
        "resource_caps",
        "start_update",
        "stop_update",
        "resume_checkpoint",
        "scientific_branch",
    }
)


@dataclass(frozen=True)
class B1WorkerInvocation:
    request: B1ArmSeedRequest
    attempt_root: Path
    start_update: int
    stop_update: int
    resume_checkpoint: Path | None


def encode_worker_request(
    request: B1ArmSeedRequest,
    *,
    attempt_root: Path,
    start_update: int,
    stop_update: int,
    resume_checkpoint: Path | None,
) -> dict[str, Any]:
    """Return the one strict JSON request shape accepted by this worker."""

    request.__post_init__()
    root = attempt_root.resolve(strict=False)
    scratch = ensure_confined(request.scratch_root, root)
    durable = ensure_confined(request.durable_root, root)
    receipt = ensure_confined(request.admission_receipt_path, root)
    resume = (
        None
        if resume_checkpoint is None
        else str(ensure_confined(resume_checkpoint, root))
    )
    return {
        "schema": WORKER_REQUEST_SCHEMA,
        "attempt_root": str(root),
        "attempt_id": request.attempt_id,
        "arm": request.arm,
        "seed": request.seed,
        "train_episode_ids": list(request.train_episode_ids),
        "checkpoint_updates": list(request.checkpoint_updates),
        "eval_stochastic_ids": list(request.eval_stochastic_ids),
        "eval_motif_ids": list(request.eval_motif_ids),
        "scratch_root": str(scratch),
        "durable_root": str(durable),
        "admission_schema": request.admission_schema,
        "admission_receipt_path": str(receipt),
        "admission_receipt_sha256": request.admission_receipt_sha256,
        "implementation_commit": request.implementation_commit,
        "source_conformance_sha256": request.source_conformance_sha256,
        "resource_caps": request.resource_caps.as_dict(),
        "start_update": start_update,
        "stop_update": stop_update,
        "resume_checkpoint": resume,
        "scientific_branch": None,
    }


def _atomic_create_json(path: Path, value: Mapping[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"create-only B1 worker record exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".hmasd-b1-json-", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical_json_bytes(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def wrap_worker_result(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Keep process-transport identity separate from raw engine evidence."""

    if (
        not isinstance(raw, Mapping)
        or raw.get("schema") != B1_RAW_EVIDENCE_SCHEMA
        or raw.get("scientific_branch", object()) is not None
    ):
        raise ValueError("B1 worker raw evidence identity differs")
    return {
        "schema": WORKER_RESULT_SCHEMA,
        "raw_evidence": raw,
        "scientific_branch": None,
    }


def load_worker_request(path: Path) -> B1WorkerInvocation:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("B1 worker request is unreadable") from exc
    if not isinstance(payload, dict) or frozenset(payload) != _REQUEST_KEYS:
        raise ValueError("B1 worker request schema is incomplete or extended")
    if payload["schema"] != WORKER_REQUEST_SCHEMA or payload["scientific_branch"] is not None:
        raise ValueError("B1 worker request identity differs")
    attempt_root = Path(payload["attempt_root"]).resolve(strict=False)
    scratch = ensure_confined(Path(payload["scratch_root"]), attempt_root)
    durable = ensure_confined(Path(payload["durable_root"]), attempt_root)
    receipt = ensure_confined(Path(payload["admission_receipt_path"]), attempt_root)
    raw_resume = payload["resume_checkpoint"]
    if raw_resume is not None and type(raw_resume) is not str:
        raise ValueError("B1 resume checkpoint must be null or a path string")
    resume = (
        None
        if raw_resume is None
        else ensure_confined(Path(raw_resume), attempt_root)
    )
    request = B1ArmSeedRequest(
        plan=B1Plan(),
        attempt_id=payload["attempt_id"],
        arm=payload["arm"],
        seed=payload["seed"],
        train_episode_ids=tuple(payload["train_episode_ids"]),
        checkpoint_updates=tuple(payload["checkpoint_updates"]),
        eval_stochastic_ids=tuple(payload["eval_stochastic_ids"]),
        eval_motif_ids=tuple(payload["eval_motif_ids"]),
        scratch_root=scratch,
        durable_root=durable,
        admission_schema=payload["admission_schema"],
        admission_receipt_path=receipt,
        admission_receipt_sha256=payload["admission_receipt_sha256"],
        implementation_commit=payload["implementation_commit"],
        source_conformance_sha256=payload["source_conformance_sha256"],
        resource_caps=ResourceCaps(**payload["resource_caps"]),
        scientific_branch=None,
    )
    return B1WorkerInvocation(
        request=request,
        attempt_root=attempt_root,
        start_update=payload["start_update"],
        stop_update=payload["stop_update"],
        resume_checkpoint=resume,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--error", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        invocation = load_worker_request(args.request.resolve())
        result_path = ensure_confined(args.result.resolve(), invocation.attempt_root)
        error_path = ensure_confined(args.error.resolve(), invocation.attempt_root)
        if result_path == error_path:
            raise ValueError("B1 worker result and error paths must be distinct")
        raw = b1_engine().run_slice(
            invocation.request,
            start_update=invocation.start_update,
            stop_update=invocation.stop_update,
            resume_checkpoint=invocation.resume_checkpoint,
        )
        _atomic_create_json(result_path, wrap_worker_result(raw))
        return 0
    except BaseException as exc:
        try:
            _atomic_create_json(
                args.error.resolve(),
                {
                    "schema": WORKER_ERROR_SCHEMA,
                    "exception_type": type(exc).__name__,
                    "detail": str(exc),
                    "traceback": traceback.format_exc(),
                    "scientific_branch": None,
                },
            )
        except BaseException:
            pass
        print(f"OMRC B1 worker failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "B1WorkerInvocation",
    "WORKER_ERROR_SCHEMA",
    "WORKER_REQUEST_SCHEMA",
    "WORKER_RESULT_SCHEMA",
    "encode_worker_request",
    "load_worker_request",
    "main",
    "wrap_worker_result",
]
