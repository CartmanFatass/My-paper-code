"""Admitted noninjectable replay worker for one OMRC B1 arm-seed slot.

Formal command::

    python -m experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_policy_replay_worker --request REQUEST.json

The bound admission is validated before any host, tape, or model construction.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import traceback
from typing import Any, Mapping, Sequence

from . import addressing
from .artifact import canonical_json_bytes, ensure_confined
from .b0 import ARMS, MIN_AVAILABLE_BYTES, validate_memory_receipt
from .b1_contract import (
    B1_BOUND_ADMISSION_SCHEMA,
    B1_CHECKPOINT_UPDATES,
    B1_EVAL_MOTIF_IDS,
    B1_EVAL_STOCHASTIC_IDS,
    B1_RUN_NAME,
    B1_SLOT_ORDER,
)
from .b1_metrics_policy_assembly import (
    ONE_SLOT_FORMAL_SCHEMA,
    ONE_SLOT_TEST_ONLY_SCHEMA,
    assemble_one_slot_policy_tables,
)


POLICY_REPLAY_REQUEST_SCHEMA = "cbsc_omrc_b01_policy_replay_request_v1"
POLICY_REPLAY_TEST_REQUEST_SCHEMA = "cbsc_omrc_b01_policy_replay_test_request_v1"
POLICY_REPLAY_RESULT_SCHEMA = "cbsc_omrc_b01_policy_replay_result_v1"
POLICY_REPLAY_TEST_RESULT_SCHEMA = "cbsc_omrc_b01_policy_replay_test_result_v1"
POLICY_REPLAY_ERROR_SCHEMA = "cbsc_omrc_b01_policy_replay_error_v1"
CANONICAL_REPO_ROOT = Path(__file__).resolve().parents[4]
CANONICAL_PREFLIGHT = (
    CANONICAL_REPO_ROOT / "scripts" / "hmasd_resource_preflight.py"
).resolve(strict=True)

_REQUEST_FIELDS = frozenset(
    {
        "schema", "attempt_root", "attempt_id", "run_name", "seed", "arm",
        "original_slot_index", "checkpoint_inventory", "implementation_commit",
        "source_conformance_sha256", "literal_binding_spec_sha256",
        "source_evaluations", "source_evaluations_sha256", "source_active_modes",
        "eval_stochastic_ids", "eval_motif_ids", "admission_receipt_path",
        "admission_receipt_sha256", "scratch_root", "output_path", "error_path",
        "scientific_branch",
    }
)
_BOUND_ADMISSION_FIELDS = frozenset(
    {
        "schema", "attempt_id", "run_name", "arm", "seed",
        "implementation_commit", "source_conformance_sha256",
        "bound_receipt_path", "raw_output_path", "python_executable",
        "python_sha256", "preflight_script", "preflight_script_sha256",
        "exact_command", "raw_receipt_sha256", "receipt",
    }
)


class PolicyReplayWorkerError(ValueError):
    """A replay request, admission, or publication boundary differs."""


@dataclass(frozen=True)
class PolicyReplayInvocation:
    attempt_root: Path
    attempt_id: str
    seed: int
    arm: str
    original_slot_index: int
    checkpoint_inventory: tuple[dict[str, Any], ...]
    implementation_commit: str
    source_conformance_sha256: str
    literal_binding_spec_sha256: str
    source_evaluations: tuple[dict[str, Any], ...]
    source_evaluations_sha256: str
    source_active_modes: tuple[str, ...]
    eval_stochastic_ids: tuple[int, ...]
    eval_motif_ids: tuple[int, ...]
    admission_receipt_path: Path
    admission_receipt_sha256: str
    scratch_root: Path
    output_path: Path
    error_path: Path
    test_only: bool


def _require_digest(name: str, value: object, length: int = 64) -> str:
    if (
        type(value) is not str
        or len(value) != length
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise PolicyReplayWorkerError(f"{name} digest differs")
    return value


def _validate_compact_inventory(
    value: Sequence[Mapping[str, Any]], *, root: Path
) -> tuple[dict[str, Any], ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes, bytearray))
        or len(value) != len(B1_CHECKPOINT_UPDATES)
    ):
        raise PolicyReplayWorkerError("checkpoint inventory must be a sequence")
    output: list[dict[str, Any]] = []
    for update, record in zip(B1_CHECKPOINT_UPDATES, value, strict=True):
        if not isinstance(record, Mapping) or set(record) != {"update", "path", "sha256"}:
            raise PolicyReplayWorkerError("checkpoint inventory schema differs")
        if record["update"] != update:
            raise PolicyReplayWorkerError("checkpoint inventory order differs")
        path = ensure_confined(Path(record["path"]), root)
        output.append(
            {
                "update": update,
                "path": str(path),
                "sha256": _require_digest("checkpoint SHA", record["sha256"]),
            }
        )
    if len(output) != len(B1_CHECKPOINT_UPDATES):
        raise PolicyReplayWorkerError("checkpoint inventory coverage differs")
    return tuple(output)


def encode_policy_replay_request(
    *,
    attempt_root: Path,
    attempt_id: str,
    seed: int,
    arm: str,
    original_slot_index: int,
    checkpoint_inventory: Sequence[Mapping[str, Any]],
    implementation_commit: str,
    source_conformance_sha256: str,
    literal_binding_spec_sha256: str,
    source_evaluations: Sequence[Mapping[str, Any]],
    source_active_modes: Sequence[str],
    admission_receipt_path: Path,
    admission_receipt_sha256: str,
    scratch_root: Path,
    output_path: Path,
    error_path: Path,
    test_only: bool = False,
) -> dict[str, Any]:
    root = Path(attempt_root).resolve(strict=True)
    if type(test_only) is not bool or type(attempt_id) is not str or not attempt_id:
        raise PolicyReplayWorkerError("replay request profile/attempt differs")
    if (
        type(original_slot_index) is not int
        or original_slot_index not in range(len(B1_SLOT_ORDER))
        or B1_SLOT_ORDER[original_slot_index] != (seed, arm)
    ):
        raise PolicyReplayWorkerError("replay request slot identity differs")
    test_identities = {(21101, "RAW-GRU", 1), (21121, "RAW-GRU", 5), (21143, "RAW-GRU", 9)}
    if test_only and (seed, arm, original_slot_index) not in test_identities:
        raise PolicyReplayWorkerError("TEST_ONLY replay identity differs")
    inventory = _validate_compact_inventory(checkpoint_inventory, root=root)
    receipt = ensure_confined(admission_receipt_path, root)
    scratch = ensure_confined(scratch_root, root)
    output = ensure_confined(output_path, root)
    error = ensure_confined(error_path, root)
    if len({receipt, scratch, output, error}) != 4 or output == error:
        raise PolicyReplayWorkerError("replay request paths overlap")
    stochastic_ids = (0,) if test_only else B1_EVAL_STOCHASTIC_IDS
    motif_ids = (0,) if test_only else B1_EVAL_MOTIF_IDS
    if (
        not isinstance(source_evaluations, Sequence)
        or isinstance(source_evaluations, (str, bytes, bytearray))
        or len(source_evaluations) != len(B1_CHECKPOINT_UPDATES)
        or not isinstance(source_active_modes, Sequence)
        or isinstance(source_active_modes, (str, bytes, bytearray))
        or any(type(mode) is not str or not mode for mode in source_active_modes)
    ):
        raise PolicyReplayWorkerError("source held-out evidence binding differs")
    source_values = [dict(record) for record in source_evaluations]
    source_sha = hashlib.sha256(canonical_json_bytes(source_values)).hexdigest()
    return {
        "schema": (
            POLICY_REPLAY_TEST_REQUEST_SCHEMA if test_only else POLICY_REPLAY_REQUEST_SCHEMA
        ),
        "attempt_root": str(root),
        "attempt_id": attempt_id,
        "run_name": B1_RUN_NAME,
        "seed": seed,
        "arm": arm,
        "original_slot_index": original_slot_index,
        "checkpoint_inventory": list(inventory),
        "implementation_commit": _require_digest(
            "implementation commit", implementation_commit, 40
        ),
        "source_conformance_sha256": _require_digest(
            "source conformance", source_conformance_sha256
        ),
        "literal_binding_spec_sha256": _require_digest(
            "literal binding specification", literal_binding_spec_sha256
        ),
        "source_evaluations": source_values,
        "source_evaluations_sha256": source_sha,
        "source_active_modes": list(source_active_modes),
        "eval_stochastic_ids": list(stochastic_ids),
        "eval_motif_ids": list(motif_ids),
        "admission_receipt_path": str(receipt),
        "admission_receipt_sha256": _require_digest(
            "admission receipt", admission_receipt_sha256
        ),
        "scratch_root": str(scratch),
        "output_path": str(output),
        "error_path": str(error),
        "scientific_branch": None,
    }


def load_policy_replay_request(path: Path) -> PolicyReplayInvocation:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PolicyReplayWorkerError("policy replay request is unreadable") from exc
    if not isinstance(value, Mapping) or frozenset(value) != _REQUEST_FIELDS:
        raise PolicyReplayWorkerError("policy replay request schema differs")
    if value["schema"] not in {
        POLICY_REPLAY_REQUEST_SCHEMA, POLICY_REPLAY_TEST_REQUEST_SCHEMA
    } or value["scientific_branch"] is not None:
        raise PolicyReplayWorkerError("policy replay request identity differs")
    test_only = value["schema"] == POLICY_REPLAY_TEST_REQUEST_SCHEMA
    root = Path(value["attempt_root"]).resolve(strict=True)
    canonical = encode_policy_replay_request(
        attempt_root=root,
        attempt_id=value["attempt_id"],
        seed=value["seed"],
        arm=value["arm"],
        original_slot_index=value["original_slot_index"],
        checkpoint_inventory=value["checkpoint_inventory"],
        implementation_commit=value["implementation_commit"],
        source_conformance_sha256=value["source_conformance_sha256"],
        literal_binding_spec_sha256=value["literal_binding_spec_sha256"],
        source_evaluations=value["source_evaluations"],
        source_active_modes=value["source_active_modes"],
        admission_receipt_path=Path(value["admission_receipt_path"]),
        admission_receipt_sha256=value["admission_receipt_sha256"],
        scratch_root=Path(value["scratch_root"]),
        output_path=Path(value["output_path"]),
        error_path=Path(value["error_path"]),
        test_only=test_only,
    )
    if dict(value) != canonical:
        raise PolicyReplayWorkerError("policy replay request canonical fields differ")
    return PolicyReplayInvocation(
        attempt_root=root,
        attempt_id=value["attempt_id"],
        seed=value["seed"],
        arm=value["arm"],
        original_slot_index=value["original_slot_index"],
        checkpoint_inventory=tuple(dict(row) for row in value["checkpoint_inventory"]),
        implementation_commit=value["implementation_commit"],
        source_conformance_sha256=value["source_conformance_sha256"],
        literal_binding_spec_sha256=value["literal_binding_spec_sha256"],
        source_evaluations=tuple(dict(row) for row in value["source_evaluations"]),
        source_evaluations_sha256=value["source_evaluations_sha256"],
        source_active_modes=tuple(value["source_active_modes"]),
        eval_stochastic_ids=tuple(value["eval_stochastic_ids"]),
        eval_motif_ids=tuple(value["eval_motif_ids"]),
        admission_receipt_path=Path(value["admission_receipt_path"]),
        admission_receipt_sha256=value["admission_receipt_sha256"],
        scratch_root=Path(value["scratch_root"]),
        output_path=Path(value["output_path"]),
        error_path=Path(value["error_path"]),
        test_only=test_only,
    )


def _validate_fresh_admission(invocation: PolicyReplayInvocation) -> dict[str, Any]:
    path = invocation.admission_receipt_path
    if not path.is_file():
        raise PolicyReplayWorkerError("fresh bound admission receipt is absent")
    before = path.read_bytes()
    if hashlib.sha256(before).hexdigest() != invocation.admission_receipt_sha256:
        raise PolicyReplayWorkerError("fresh bound admission receipt SHA differs")
    try:
        bound = json.loads(before)
    except json.JSONDecodeError as exc:
        raise PolicyReplayWorkerError("fresh bound admission receipt is unreadable") from exc
    if not isinstance(bound, Mapping) or frozenset(bound) != _BOUND_ADMISSION_FIELDS:
        raise PolicyReplayWorkerError("fresh bound admission schema differs")
    if (
        bound["schema"] != B1_BOUND_ADMISSION_SCHEMA
        or bound["attempt_id"] != invocation.attempt_id
        or bound["run_name"] != B1_RUN_NAME
        or bound["seed"] != invocation.seed
        or bound["arm"] != invocation.arm
        or bound["implementation_commit"] != invocation.implementation_commit
        or bound["source_conformance_sha256"] != invocation.source_conformance_sha256
        or Path(bound["bound_receipt_path"]).resolve(strict=False) != path.resolve()
    ):
        raise PolicyReplayWorkerError("fresh bound admission identity is stale")
    executable = Path(sys.executable).resolve()
    preflight = CANONICAL_PREFLIGHT
    raw_path = Path(bound["raw_output_path"]).resolve(strict=True)
    if (
        bound["python_executable"] != str(executable)
        or bound["python_sha256"] != hashlib.sha256(executable.read_bytes()).hexdigest()
        or bound["preflight_script"] != str(preflight)
        or bound["preflight_script_sha256"] != hashlib.sha256(preflight.read_bytes()).hexdigest()
        or bound["exact_command"] != [
            str(executable), str(preflight), "admit-memory", "--out", str(raw_path)
        ]
        or bound["raw_receipt_sha256"] != hashlib.sha256(raw_path.read_bytes()).hexdigest()
    ):
        raise PolicyReplayWorkerError("fresh bound admission executable/raw binding differs")
    try:
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        receipt = validate_memory_receipt(bound["receipt"])
        raw_receipt = validate_memory_receipt(raw)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise PolicyReplayWorkerError("fresh bound admission did not pass both 4-GiB floors") from exc
    if receipt != raw_receipt or (
        receipt["available_physical_bytes"] < MIN_AVAILABLE_BYTES
        or receipt["effective_available_bytes"] < MIN_AVAILABLE_BYTES
    ):
        raise PolicyReplayWorkerError("fresh bound admission did not pass both 4-GiB floors")
    if path.read_bytes() != before:
        raise PolicyReplayWorkerError("fresh bound admission changed during validation")
    return dict(bound)


def _atomic_create_json(path: Path, value: Mapping[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"create-only policy replay output exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".hmasd-policy-replay-", suffix=".tmp", dir=path.parent
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


def run_policy_replay(invocation: PolicyReplayInvocation) -> dict[str, Any]:
    if invocation.output_path.exists():
        raise FileExistsError(
            f"create-only policy replay output exists: {invocation.output_path}"
        )
    bound_admission = _validate_fresh_admission(invocation)
    if not invocation.scratch_root.is_dir():
        raise PolicyReplayWorkerError("confined replay scratch root is absent")

    # Admission precedes these imports and every host/tape/model construction.
    from .host import DynamicHost

    host = DynamicHost(B1_RUN_NAME, invocation.seed)
    tapes = tuple(
        host.build_stochastic(addressing.EVAL_STOCHASTIC, tape_id)
        for tape_id in invocation.eval_stochastic_ids
    ) + tuple(host.build_motif(tape_id) for tape_id in invocation.eval_motif_ids)
    packet = assemble_one_slot_policy_tables(
        staging_root=invocation.attempt_root,
        attempt_id=invocation.attempt_id,
        seed=invocation.seed,
        arm=invocation.arm,
        original_slot_index=invocation.original_slot_index,
        checkpoint_inventory=invocation.checkpoint_inventory,
        source_evaluations=invocation.source_evaluations,
        source_active_modes=invocation.source_active_modes,
        heldout_tapes=tapes,
        implementation_commit=invocation.implementation_commit,
        source_conformance_sha256=invocation.source_conformance_sha256,
        literal_binding_spec_sha256=invocation.literal_binding_spec_sha256,
        test_only=invocation.test_only,
    )
    expected_packet_schema = (
        ONE_SLOT_TEST_ONLY_SCHEMA if invocation.test_only else ONE_SLOT_FORMAL_SCHEMA
    )
    if packet["schema"] != expected_packet_schema:
        raise PolicyReplayWorkerError("one-slot replay packet schema differs")
    wrapper_body = {
        "schema": (
            POLICY_REPLAY_TEST_RESULT_SCHEMA
            if invocation.test_only
            else POLICY_REPLAY_RESULT_SCHEMA
        ),
        "test_only": invocation.test_only,
        "run_name": B1_RUN_NAME,
        "attempt_id": invocation.attempt_id,
        "seed": invocation.seed,
        "arm": invocation.arm,
        "original_slot_index": invocation.original_slot_index,
        "admission_receipt_sha256": invocation.admission_receipt_sha256,
        "admission_binding": {
            "schema": bound_admission["schema"],
            "attempt_id": bound_admission["attempt_id"],
            "run_name": bound_admission["run_name"],
            "seed": bound_admission["seed"],
            "arm": bound_admission["arm"],
            "implementation_commit": bound_admission["implementation_commit"],
            "source_conformance_sha256": bound_admission["source_conformance_sha256"],
            "receipt_sha256": invocation.admission_receipt_sha256,
            "available_physical_bytes": bound_admission["receipt"]["available_physical_bytes"],
            "effective_available_bytes": bound_admission["receipt"]["effective_available_bytes"],
        },
        "implementation_commit": invocation.implementation_commit,
        "source_conformance_sha256": invocation.source_conformance_sha256,
        "literal_binding_spec_sha256": invocation.literal_binding_spec_sha256,
        "checkpoint_inventory": [dict(row) for row in invocation.checkpoint_inventory],
        "source_evaluations_sha256": invocation.source_evaluations_sha256,
        "slot_packet_schema": packet["schema"],
        "policy_decisions": packet["policy_decisions"],
        "policy_curves": packet["policy_curves"],
        "execution_mode_records": packet["execution_mode_records"],
        "evaluation_join_records": packet["evaluation_join_records"],
        "literal_nulls": packet["literal_nulls"],
        "counts": packet["counts"],
        "scientific_branch": None,
        "scientific_polarity": None,
        "promotion_eligible": None,
        "b2_extension_trigger": None,
    }
    wrapper = {
        **wrapper_body,
        "result_body_sha256": hashlib.sha256(
            canonical_json_bytes(wrapper_body)
        ).hexdigest(),
    }
    _atomic_create_json(invocation.output_path, wrapper)
    return wrapper


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    invocation: PolicyReplayInvocation | None = None
    try:
        invocation = load_policy_replay_request(args.request.resolve(strict=True))
        run_policy_replay(invocation)
        return 0
    except BaseException as exc:
        if invocation is not None:
            try:
                blocking_code = (
                    "HELDOUT_SOURCE_REPLAY_DIVERGENCE"
                    if "divergence" in str(exc).lower()
                    else "POLICY_REPLAY_WORKER_FAILURE"
                )
                _atomic_create_json(
                    invocation.error_path,
                    {
                        "schema": POLICY_REPLAY_ERROR_SCHEMA,
                        "test_only": invocation.test_only,
                        "attempt_id": invocation.attempt_id,
                        "seed": invocation.seed,
                        "arm": invocation.arm,
                        "original_slot_index": invocation.original_slot_index,
                        "exception_type": type(exc).__name__,
                        "detail": str(exc),
                        "blocking_audit_codes": [blocking_code],
                        "traceback": traceback.format_exc(),
                        "scientific_branch": None,
                    },
                )
            except BaseException:
                pass
        print(f"OMRC B1 policy replay worker failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "POLICY_REPLAY_ERROR_SCHEMA",
    "CANONICAL_PREFLIGHT",
    "CANONICAL_REPO_ROOT",
    "POLICY_REPLAY_REQUEST_SCHEMA",
    "POLICY_REPLAY_RESULT_SCHEMA",
    "POLICY_REPLAY_TEST_REQUEST_SCHEMA",
    "POLICY_REPLAY_TEST_RESULT_SCHEMA",
    "PolicyReplayInvocation",
    "PolicyReplayWorkerError",
    "encode_policy_replay_request",
    "load_policy_replay_request",
    "main",
    "run_policy_replay",
]
