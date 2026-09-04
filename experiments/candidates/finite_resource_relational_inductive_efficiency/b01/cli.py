"""B01 contract/TEST-smoke CLI.  No production seed or result command exists."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from ..arms import initialize_paired_arms
from ..policy import FRRIEActorCritic
from ..rng import AddressedRNG
from ..training import make_optimizer
from .checkpoint import decode_checkpoint, snapshot_runtime
from .constants import CHECKPOINTS, EXPERIMENT_ID, LEARNED_ARMS
from .contract import (
    B01ContractError, bind_invocation_resource, canonical_json_bytes,
    validate_manifest, validate_test_manifest, validate_formal_source_gate,
)
from .lifecycle import claim_fresh_roots, publish_create_only
from .preflight import runtime_algorithm_receipt, static_algorithm_receipt
from .seed_packet import read_test_seed_packet


def _read(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _fresh(receipt: dict) -> None:
    try:
        assessed = datetime.fromisoformat(receipt["assessed_at"].replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError) as exc:
        raise B01ContractError("TEST smoke receipt assessed_at is invalid") from exc
    age = (datetime.now(timezone.utc) - assessed.astimezone(timezone.utc)).total_seconds()
    if not 0 <= age <= 120:
        raise B01ContractError("TEST smoke requires an adjacent <=120-second memory receipt")


def _empty_work() -> dict:
    row = {
        "training_update": 0, "episodes": 0, "environment_slots": 0,
        "backward_calls": 0, "adam_steps": 0, "native_batch_calls": 0,
        "native_batch_ledger": {
            "reset_calls": 0, "observe_calls": 0, "step_calls": 0,
            "environment_slots": 0,
        },
        "worker_count": 4, "thread_count": 1,
    }
    return {arm: dict(row, native_batch_ledger=dict(row["native_batch_ledger"])) for arm in LEARNED_ARMS}


def _zero_audit() -> dict:
    return {
        "first_tight_contact_update": None, "precontact_full_state_equal": True,
        "tight_projection_changed_coordinates": 0, "wide_boundary_contact": False,
        "maximum_tight_overshoot": 0.0, "cumulative_tight_displacement": 0.0,
    }


def _smoke(manifest_path: str, receipt_path: str) -> int:
    manifest = validate_test_manifest(_read(manifest_path))
    receipt = _read(receipt_path)
    _fresh(receipt)
    binding = bind_invocation_resource(
        invocation_id="FRRIE-B01-TEST-SMOKE", operation="TEST_SMOKE",
        receipt_path=Path(receipt_path).resolve(), receipt=receipt, test_only=True,
    )
    packet = read_test_seed_packet(manifest["seed_packet"]["path"])
    root = bytes.fromhex(packet["roots_hex"][0])
    phy, edge = initialize_paired_arms(
        AddressedRNG(root), manifest["seed_label"],
    )
    models = {
        "PHY_TRUST": FRRIEActorCritic(phy), "EDGE_FLEX": FRRIEActorCritic(edge),
    }
    optimizers = {arm: make_optimizer(models[arm]) for arm in LEARNED_ARMS}
    algorithm = runtime_algorithm_receipt(models, optimizers)
    checkpoint0 = snapshot_runtime(
        manifest=manifest, seed_label=manifest["seed_label"], update=0,
        models=models, optimizers=optimizers, work=_empty_work(),
        invocation_binding=binding, projection_audit=_zero_audit(),
    )
    roots = claim_fresh_roots(manifest)
    checkpoint_path = publish_create_only(
        roots["checkpoint"] / "checkpoint-000.json", checkpoint0,
    )
    persisted_checkpoint = checkpoint_path.read_bytes()
    if persisted_checkpoint != checkpoint0:
        raise B01ContractError("persisted checkpoint0 bytes differ from staged bytes")
    restored = decode_checkpoint(
        persisted_checkpoint, manifest=manifest, expected_seed_label=manifest["seed_label"],
        expected_update=0, expected_test_only=True,
    )
    if any(restored["arm_state_bytes"][arm] != models[arm].parameter_bytes() for arm in LEARNED_ARMS):
        raise B01ContractError("persisted checkpoint0 decode differs from live TEST models")
    publish_create_only(roots["output"] / "smoke.json", {
        "schema": "FRRIE_B01_CONTRACT_CHECKPOINT_SMOKE_V1", "manifest_contract": manifest,
        "invocation_binding": binding, "algorithm_preflight": algorithm,
        "checkpoint0_persisted_readback_decode_revalidated": True,
        "performance_disposition": "REPAIR_REQUIRED",
        "blocker": "PACKAGE_NATIVE_EQUIVALENCE_AND_END_TO_END_TELEMETRY_NOT_COMPLETE",
        "scientific_values": None, "complete": True,
        "native_executed": False, "environment_executed": False, "update_executed": False,
        "evaluation_executed": False,
    })
    print(canonical_json_bytes({
        "status": "TEST_CONTRACT_SMOKE_COMPLETE_REPAIR_REQUIRED",
        "output": str(roots["output"]),
    }).decode("ascii"))
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="frrie-b01")
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("describe")
    check = commands.add_parser("check")
    check.add_argument("--manifest", required=True)
    check.add_argument("--test-only", action="store_true")
    source = commands.add_parser("formal-source-check")
    source.add_argument("--manifest", required=True)
    smoke = commands.add_parser("test-smoke")
    smoke.add_argument("--manifest", required=True)
    smoke.add_argument("--receipt", required=True)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "describe":
            print(canonical_json_bytes({
                "experiment_id": EXPERIMENT_ID, "checkpoints": list(CHECKPOINTS),
                "static_algorithm_preflight": static_algorithm_receipt(),
                "production_seed_creator_cli_exposed": False,
                "result_bearing_command_exposed": False,
            }).decode("ascii"))
            return 0
        if args.command == "check":
            manifest = _read(args.manifest)
            validated = validate_test_manifest(manifest) if args.test_only else validate_manifest(manifest)
            print(canonical_json_bytes(validated).decode("ascii"))
            return 0
        if args.command == "formal-source-check":
            print(canonical_json_bytes(
                validate_formal_source_gate(_read(args.manifest))
            ).decode("ascii"))
            return 0
        return _smoke(args.manifest, args.receipt)
    except (B01ContractError, OSError, json.JSONDecodeError) as exc:
        print(f"B01 refused: {exc}")
        return 2
