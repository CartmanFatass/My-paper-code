"""Fail-closed production guard and paired logical-work receipts.

No production trainer is supplied by this result-blind scaffold.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .contracts.core import (
    FRRIE_SEALED_SEED_PACKET_V1, LEARNED_ARMS, ContractError,
    manifest_packet_contract, validate_manifest,
)
from .host import (
    NativeBackendUnavailable, NativePreflightFailed, TestOnlyNativeBackend,
    admit_native_backend, preflight_native_backend,
)


class SealedInputMissing(ContractError):
    pass


class ResumeContractMismatch(ContractError):
    pass


class ProductionTrainingUnavailable(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class WorkReceipt:
    arm_id: str
    update: int
    environment_slots: int
    learned_decisions: int
    backward_calls: int
    adam_steps: int
    parameter_bytes: int
    flops: int
    workers: int
    threads: int
    native_width: int
    dtype: str
    checkpoint_io: int
    evaluation_opportunities: int
    tape_contract: Mapping[str, Any]

    def parity_vector(self) -> tuple[Any, ...]:
        row = asdict(self)
        return tuple(value for field, value in row.items() if field not in {"arm_id"})


def audit_pair_parity(left: WorkReceipt, right: WorkReceipt) -> None:
    if {left.arm_id, right.arm_id} != set(LEARNED_ARMS):
        raise ContractError("pair receipt must contain exactly both learned arms")
    if left.parity_vector() != right.parity_vector():
        raise ContractError("paired logical/native work or tape receipt differs")


def validate_sealed_seed_packet(packet: Mapping[str, Any], manifest: Mapping[str, Any]) -> dict[str, Any]:
    required = {"schema", "manifest_contract", "blocks", "sealed_payload", "sealed", "complete"}
    if not isinstance(packet, Mapping) or set(packet) != required:
        raise SealedInputMissing("sealed seed packet fields must be exact")
    if packet["schema"] != FRRIE_SEALED_SEED_PACKET_V1 or packet["sealed"] is not True or packet["complete"] is not True:
        raise SealedInputMissing("seed packet is not sealed and complete")
    if packet["manifest_contract"] != manifest_packet_contract(manifest):
        raise SealedInputMissing("seed packet manifest contract mismatch")
    if packet["blocks"] != manifest["seed_blocks"]:
        raise SealedInputMissing("seed packet block labels mismatch")
    sealed_payload = packet["sealed_payload"]
    if not isinstance(sealed_payload, Mapping) or set(sealed_payload) != set(packet["blocks"]):
        raise SealedInputMissing("seed packet sealed payload is partial")
    if any(not isinstance(value, str) or not value for value in sealed_payload.values()):
        raise SealedInputMissing("seed packet sealed payload entries must be opaque nonempty strings")
    return dict(packet)


def guard_production_run(
    manifest0: Mapping[str, Any], *, backend: Any, seed_packet: Mapping[str, Any] | None,
    resume_contract: Mapping[str, Any] | None = None,
) -> None:
    """Check the direct production contracts, then stop because no trainer exists."""
    manifest = validate_manifest(manifest0)
    if seed_packet is None:
        raise SealedInputMissing("a sealed seed packet is required")
    packet = validate_sealed_seed_packet(seed_packet, manifest)
    packet_path = Path(manifest["sealed_seed_packet"]["path"])
    try:
        persisted_packet = json.loads(packet_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SealedInputMissing("bound sealed packet is absent or unreadable") from exc
    if persisted_packet != packet:
        raise SealedInputMissing("caller and create-only sealed packet structures differ")
    native = admit_native_backend(backend, production=True)
    native_contract = native.contract
    host_binding = manifest["host"]
    if (
        native_contract.host_id != host_binding["id"] or native_contract.source_id != host_binding["source_id"]
        or native_contract.component != host_binding["component"] or native_contract.abi != host_binding["abi"]
        or native_contract.binding_kind != host_binding["binding_kind"]
        or native_contract.python_fallback != host_binding["python_fallback"]
    ):
        raise NativeBackendUnavailable("native contract does not equal the manifest host contract")
    compute = manifest["compute"]
    if (native_contract.native_width, native_contract.workers, native_contract.threads) != (
        compute["native_width"], compute["workers"], compute["threads"],
    ):
        raise NativeBackendUnavailable("native resource contract does not equal the manifest")
    if (
        native_contract.device != compute["device"]
        or native_contract.dtype != compute["model_dtype"]
        or native_contract.reduction_dtype != compute["reduction_dtype"]
    ):
        raise NativeBackendUnavailable("native numeric contract does not equal the manifest")
    receipt = preflight_native_backend(native, manifest["resource_ceiling"])
    receipt_path = Path(manifest["preflight_receipt"]["path"])
    try:
        sealed_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise NativePreflightFailed("preflight receipt is absent or unreadable") from exc
    if sealed_receipt != receipt:
        raise NativePreflightFailed("runtime preflight does not equal the bound fresh receipt")
    if resume_contract is not None:
        expected = {
            "manifest_contract": manifest,
            "native_contract": asdict(native_contract),
            "seed_packet_contract": packet,
        }
        if dict(resume_contract) != expected:
            raise ResumeContractMismatch("resume contract does not exactly match manifest/native/seed")
    raise ProductionTrainingUnavailable(
        "result-blind scaffold has no production FRRIE trainer; no scientific activity started"
    )


def run_test_only_chain(*, steps: int = 2) -> dict[str, Any]:
    """Bounded structural smoke chain, never admitted as production evidence."""
    if isinstance(steps, bool) or not isinstance(steps, int) or not 1 <= steps <= 8:
        raise ContractError("TEST_ONLY chain steps must be in [1,8]")
    backend = TestOnlyNativeBackend()
    admit_native_backend(backend, production=False)
    preflight_native_backend(backend, {"wall_seconds": 1})
    trajectory_contracts = []
    for step in range(steps):
        row = backend.rollout({"trajectory_kind": "SHADOW", "allow_side_effects": False, "step": step})
        if row["side_effect_count"] != 0:
            raise ContractError("TEST_ONLY shadow side effect")
        trajectory_contracts.append(row)
    from .arms import initialize_paired_arms
    from .checkpoint import restore_checkpoint, serialize_checkpoint
    from .rng import AddressedRNG, RNGAddress
    phy, edge = initialize_paired_arms(AddressedRNG(b"T" * 32), "FRRIE-TEST-ONLY-BLOCK")
    if phy.parameter_bytes() != edge.parameter_bytes():
        raise ContractError("TEST_ONLY pair initialization mismatch")
    rng = AddressedRNG(b"T" * 32)
    address = RNGAddress("TEST_ONLY", "TEST_ONLY", 1, 0, 0, 0, 0, 0, "TEST_ONLY")
    tape = [
        {"address": coordinate, "word_hex": word.hex()}
        for coordinate, word in rng.tape_words(address)
    ]
    test_work = {
        arm: {
            "arm_id": arm, "update": 0, "environment_slots": 0,
            "learned_decisions": 0, "backward_calls": 0, "adam_steps": 0,
            "parameter_bytes": 142052, "flops": 0, "workers": 1,
            "threads": 1, "native_width": 1, "dtype": "float32",
            "checkpoint_io": 0, "evaluation_opportunities": 0,
            "tape_contract": {"schema": "TEST_ONLY_TAPE_V1", "coordinates": [0]},
        }
        for arm in LEARNED_ARMS
    }
    checkpoint = serialize_checkpoint(
        manifest_contract={"schema": "TEST_ONLY_MANIFEST_V1"},
        native_contract={"schema": "TEST_ONLY_NATIVE_V1"},
        seed_packet_contract={"schema": "TEST_ONLY_SEED_PACKET_V1"},
        update=0, frontiers={
            "training_update": 0, "minibatch_cursor": 0,
            "environment_cursor": 0, "evaluation_checkpoint_cursor": 0,
        },
        arm_state_bytes={"PHY_TRUST": b"p", "EDGE_FLEX": b"e"},
        optimizer_state_bytes={"PHY_TRUST": b"op", "EDGE_FLEX": b"oe"},
        work_receipts=test_work,
        rng_frontier={
            "schema": "FRRIE_STATELESS_RNG_FRONTIER_V1",
            "stateless": True, "tape_contract": tape,
        },
    )
    restore_checkpoint(
        checkpoint, manifest_contract={"schema": "TEST_ONLY_MANIFEST_V1"},
        native_contract={"schema": "TEST_ONLY_NATIVE_V1"},
        seed_packet_contract={"schema": "TEST_ONLY_SEED_PACKET_V1"}, expected_update=0,
    )
    return {
        "schema": "TEST_ONLY_FRRIE_CHAIN_V1", "TEST_ONLY": True,
        "production_admissible": False, "steps": steps,
        "trajectory_contracts": trajectory_contracts,
    }
