"""Internal canonical child-process entry for one admitted OMRC B0 arm."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import traceback
from typing import Any, Mapping

from .artifact import canonical_json_bytes, ensure_confined
from .b0 import B0ArmRequest, B0Plan, ResourceCaps, validate_bound_admission
from .engine import b0_engine


WORKER_REQUEST_SCHEMA = "cbsc_omrc_b01_b0_worker_request_v1"


def _atomic_create_json(path: Path, value: Mapping[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"create-only worker result exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
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


def _load_request(path: Path) -> B0ArmRequest:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("worker request is unreadable") from exc
    if payload.get("schema") != WORKER_REQUEST_SCHEMA:
        raise ValueError("worker request schema differs")
    attempt_root = Path(payload["attempt_root"]).resolve(strict=False)
    scratch = ensure_confined(Path(payload["scratch_root"]), attempt_root)
    durable = ensure_confined(Path(payload["durable_root"]), attempt_root)
    receipt_path = ensure_confined(Path(payload["admission_receipt_path"]), attempt_root)
    receipt = validate_bound_admission(
        json.loads(receipt_path.read_text(encoding="utf-8")),
        expected_attempt_id=payload["attempt_id"],
        expected_arm=payload["arm"],
        expected_commit=payload["implementation_commit"],
        expected_receipt_path=receipt_path,
    )
    return B0ArmRequest(
        plan=B0Plan(),
        arm=payload["arm"],
        seed=payload["seed"],
        train_episode_ids=tuple(payload["train_episode_ids"]),
        eval_stochastic_ids=tuple(payload["eval_stochastic_ids"]),
        eval_motif_ids=tuple(payload["eval_motif_ids"]),
        scratch_root=scratch,
        durable_root=durable,
        admission_receipt_path=receipt_path,
        admission_receipt=receipt,
        resource_caps=ResourceCaps(**payload["resource_caps"]),
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
        request = _load_request(args.request.resolve())
        result = b0_engine().run_arm(request)
        _atomic_create_json(args.result.resolve(), dict(result))
        return 0
    except BaseException as exc:
        try:
            _atomic_create_json(
                args.error.resolve(),
                {
                    "schema": "cbsc_omrc_b01_b0_worker_error_v1",
                    "exception_type": type(exc).__name__,
                    "detail": str(exc),
                    "traceback": traceback.format_exc(),
                    "scientific_branch": None,
                },
            )
        except BaseException:
            pass
        print(f"OMRC B0 worker failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
