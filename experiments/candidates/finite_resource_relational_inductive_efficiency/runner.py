"""Fail-closed production guards and explicitly bounded TEST_ONLY chains."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .contracts.core import (
    FRRIE_SEALED_SEED_PACKET_V1, INFERENCE_CONTRACT, LEARNED_ARMS, ContractError,
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


INFERENCE_BLOCKER = "SIMULTANEOUS_MEAN_INFERENCE_UNRESOLVED_AT_24_BLOCKS"


def guard_v2_production_run(manifest0: Mapping[str, Any]) -> None:
    """Refuse current V2 result activity at its earliest semantic gate."""
    manifest = validate_manifest(manifest0)
    if manifest["inference"] == INFERENCE_CONTRACT and manifest["inference"]["status"] == INFERENCE_BLOCKER:
        raise ProductionTrainingUnavailable(INFERENCE_BLOCKER)
    raise ProductionTrainingUnavailable(
        "V2 production orchestration requires a ready prospective preflight"
    )


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
    """Legacy V1 bounded smoke retained only for explicit TEST_ONLY callers."""
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


def _clone_episode(episode: Any) -> Any:
    """Give each equal-weight TEST_ONLY batch position a distinct container."""
    from .training import RSCFEpisode
    return RSCFEpisode(**{
        field: getattr(episode, field)
        for field in (
            "roster_size", "selected_probabilities", "q_targets", "legal_masks",
            "factual_actions", "all_probabilities", "critic_values", "terminal_return",
        )
    })


def run_test_only_v2_chain(*, exercise_package_native: bool = False) -> dict[str, Any]:
    """One-update external-action V2 semantic witness, never result evidence.

    The lane deliberately uses TEST_ONLY identities and in-memory checkpoint
    bytes.  It creates no production root, seed packet, receipt, or schema and
    cannot be enlarged through arguments.
    """
    import io
    import numpy as np
    import torch

    from .arms import initialize_paired_arms
    from .evaluator import probability_vector_tv
    from .native_adapter import test_only_package_native_preflight
    from .orchestration import (
        OriginCoordinate, TestOnlyExternalEnvironment,
        assert_paired_initialization, capture_rscf_episode,
    )
    from .policy import make_actor_critic
    from .rng import AddressedRNG
    from .training import RSCFTrainer, TRAIN_ROSTER_ORDER

    native_witness: dict[str, Any]
    if exercise_package_native:
        try:
            native_witness = test_only_package_native_preflight(
                {
                    "device": "cpu", "gpu": False, "model_dtype": "float32",
                    "reduction_dtype": "float64", "native_width": 1,
                    "workers": 1, "threads": 1, "network": False,
                },
                build_if_absent=True,
            )
        except (OSError, RuntimeError) as exc:
            native_witness = {
                "schema": "TEST_ONLY_EXTERNAL_ADAPTER_FALLBACK_V2",
                "TEST_ONLY": True,
                "production_admissible": False,
                "reason": type(exc).__name__,
            }
    else:
        native_witness = {
            "schema": "TEST_ONLY_EXTERNAL_ADAPTER_FALLBACK_V2",
            "TEST_ONLY": True,
            "production_admissible": False,
            "reason": "PACKAGE_NATIVE_EXERCISE_NOT_REQUESTED",
        }

    phy_arm, edge_arm = initialize_paired_arms(
        AddressedRNG(b"V" * 32), "FRRIE-TEST-ONLY-V2-INITIALIZATION"
    )
    models = {
        "PHY_TRUST": make_actor_critic(phy_arm),
        "EDGE_FLEX": make_actor_critic(edge_arm),
    }
    assert_paired_initialization(models)
    trainers = {arm: RSCFTrainer(model) for arm, model in models.items()}
    update_receipts: dict[str, dict[str, Any]] = {}
    branch_shapes: dict[str, dict[str, list[int]]] = {}
    replay_audits: dict[str, dict[str, dict[str, Any]]] = {}
    common_uniforms: dict[int, Any] = {
        roster: np.full((12, roster), np.float32(0.5), dtype=np.float32)
        for roster in (9, 15)
    }
    for arm in LEARNED_ARMS:
        witnesses: dict[int, Any] = {}
        replay_audits[arm] = {}
        for roster in (9, 15):
            width = roster // 3
            audit: dict[str, Any] = {}
            witnesses[roster] = capture_rscf_episode(
                model=models[arm],
                environment=TestOnlyExternalEnvironment(roster),
                environment_tape={"TEST_ONLY": True, "roster": roster},
                action_uniforms=common_uniforms[roster],
                origins=(
                    OriginCoordinate(0, 0, 0),
                    OriginCoordinate(1, 0, width),
                    OriginCoordinate(2, 0, 2 * width),
                ),
                audit_out=audit,
            )
            replay_audits[arm][str(roster)] = audit
        batch = [_clone_episode(witnesses[roster]) for roster in TRAIN_ROSTER_ORDER]
        receipt = trainers[arm].update(batch)
        update_receipts[arm] = asdict(receipt)
        branch_shapes[arm] = {
            str(roster): list(witnesses[roster].q_targets.shape) for roster in (9, 15)
        }
    parity_fields = ("backward_calls", "optimizer_steps", "episodes", "roster_counts")
    if any(
        update_receipts[LEARNED_ARMS[0]][field]
        != update_receipts[LEARNED_ARMS[1]][field]
        for field in parity_fields
    ):
        raise ContractError("TEST_ONLY paired update work differs")

    # Direct arm + optimizer bytes, in-memory TEST_ONLY checkpoint roundtrip.
    state = {
        "schema": "TEST_ONLY_FRRIE_CHECKPOINT_V2",
        "TEST_ONLY": True,
        "production_admissible": False,
        "update": 1,
        "evaluation_cursor": 0,
        "arms": {arm: models[arm].parameter_bytes() for arm in LEARNED_ARMS},
        "optimizers": {},
    }
    for arm in LEARNED_ARMS:
        buffer = io.BytesIO()
        torch.save(trainers[arm].optimizer.state_dict(), buffer)
        state["optimizers"][arm] = buffer.getvalue()
    checkpoint_buffer = io.BytesIO()
    torch.save(state, checkpoint_buffer)
    checkpoint_bytes = checkpoint_buffer.getvalue()
    restored = torch.load(io.BytesIO(checkpoint_bytes), map_location="cpu", weights_only=False)
    if restored["schema"] != "TEST_ONLY_FRRIE_CHECKPOINT_V2" or restored["update"] != 1:
        raise ContractError("TEST_ONLY checkpoint roundtrip differs")
    if any(restored["arms"][arm] != state["arms"][arm] for arm in LEARNED_ARMS):
        raise ContractError("TEST_ONLY direct arm bytes changed on checkpoint roundtrip")

    # Same observation and incoming hidden; rotated shadow does not propagate.
    model = models["PHY_TRUST"]
    environment = TestOnlyExternalEnvironment(9)
    environment.reset({"TEST_ONLY": True})
    frame = environment.observe()
    observations = torch.as_tensor(frame.observations, dtype=torch.float32)
    roles = torch.as_tensor(frame.roles, dtype=torch.int64)
    incoming = model.initial_hidden(9)
    shadow_environment_before = environment.snapshot()
    intact = model.actor_step(observations, roles, incoming)
    shadow = model.shadow_step(observations, roles, incoming)
    if (not torch.equal(incoming, torch.zeros_like(incoming))
            or environment.snapshot() != shadow_environment_before):
        raise ContractError("TEST_ONLY shadow forward propagated state")
    tv = probability_vector_tv(
        intact.probabilities.detach().tolist(),
        shadow.probabilities.detach().tolist(),
        roles.tolist(),
    )
    return {
        "schema": "TEST_ONLY_FRRIE_EXTERNAL_ACTION_CHAIN_V2",
        "TEST_ONLY": True,
        "production_admissible": False,
        "updates": 1,
        "evaluation_episodes": 1,
        "native": native_witness,
        "origin_suffix_q_shapes": branch_shapes,
        "origin_suffix_audits": replay_audits,
        "paired_update_receipts": update_receipts,
        "checkpoint_roundtrip": True,
        "evaluation_adaptation": False,
        "shadow_native_steps": 0,
        "tv_reducer_shape": [len(tv)],
        "scientific_values_published": False,
    }
