from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

import pytest
import torch

from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value import (
    production_training as production_module,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value import (
    lease as lease_module,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.config import (
    CARD_REVISION,
    EventOrder,
    Regime,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.lease import (
    ActivityPermit,
    COORDINATE_PLAN_DIGEST,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.frontier import (
    CheckpointCompletion,
    CheckpointReceipt,
    FrontierContractError,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.model import (
    LearnedArm,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.native_backend import (
    SCIENCE_CARD_SHA256,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.production_training import (
    CollectedTrainingUpdate,
    ProductionTrainingError,
    ProductionTrainingService,
    TrainingRunIdentity,
    TrainingRenewalRecord,
    TrainingSourceBindings,
    _GENERATION_SCHEMA,
    _semantic_digest,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.rng import (
    EmpiricalRNG,
)


def _permit(*, sealed: bool = True) -> ActivityPermit:
    return ActivityPermit(
        lease_id="SYNTHETIC-PRODUCTION-TRAINING-LEASE",
        coordinate_plan_digest=COORDINATE_PLAN_DIGEST,
        workers=1,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        _validation_seal=lease_module._PERMIT_SEAL if sealed else None,
    )


def _bindings() -> TrainingSourceBindings:
    return TrainingSourceBindings(
        card_revision=CARD_REVISION,
        card_sha256=SCIENCE_CARD_SHA256,
        empirical_source_manifest_sha256="1" * 64,
        native_binding_digest="2" * 64,
    )


def _rng() -> EmpiricalRNG:
    # Contract-only deterministic material; no OS source, production identity,
    # model, optimizer, native execution, or checkpoint is created.
    return EmpiricalRNG(bytes(range(32)), _permit())


def _run_identity(bindings: TrainingSourceBindings | None = None) -> TrainingRunIdentity:
    return TrainingRunIdentity.create(
        master_digest="3" * 64, bindings=_bindings() if bindings is None else bindings
    )


def test_production_schedule_is_the_single_exact_training_law(tmp_path) -> None:
    service = ProductionTrainingService(
        tmp_path / "not-created",
        bindings=_bindings(),
        run_identity=_run_identity(),
    )
    assert service.production_schedule() == {
        "arms": ("TREAT", "FREE", "SET"),
        "updates_per_arm": 144,
        "episodes_per_update": 12,
        "training_k": (4, 10),
        "episodes_per_k": 6,
        "orders_per_k": {"RG": 3, "GR": 3},
        "optimizer_steps_per_update": 16,
        "optimizer_steps_per_arm": 2_304,
        "native_renewal_abi": 2,
        "python_host_fallback": False,
        "cpu_threads": 1,
        "gpu": False,
    }
    assert not service.result_root.exists()


def test_source_bindings_are_exact_and_derive_native_digest_from_lease() -> None:
    lease = {
        "card_revision": CARD_REVISION,
        "card_sha256": SCIENCE_CARD_SHA256,
        "empirical_source_manifest_sha256": "a" * 64,
        "construction_binding": {"abi_version": 2, "python_fallback": False},
    }
    derived = TrainingSourceBindings.from_lease(lease)
    assert derived.card_revision == CARD_REVISION
    assert len(derived.native_binding_digest) == 64
    with pytest.raises(ProductionTrainingError, match="card revision"):
        TrainingSourceBindings(
            "changed", SCIENCE_CARD_SHA256, "a" * 64, "b" * 64
        ).validated()


def test_prelease_fence_precedes_directory_model_and_native_activity(tmp_path) -> None:
    calls: list[str] = []

    def forbidden_native(_fixtures):
        calls.append("native")
        raise AssertionError("native boundary must not be reached")

    root = tmp_path / "result"
    service = ProductionTrainingService(
        root,
        bindings=_bindings(),
        run_identity=_run_identity(),
        native_batch_factory=forbidden_native,
    )
    with pytest.raises(Exception, match="not authorized"):
        service.create_frontier(_permit(sealed=False), _rng(), 0, "TREAT")
    assert calls == []
    assert not root.exists()


def test_update_fixture_roster_and_all_exogenous_addresses_are_arm_free() -> None:
    rng = _rng()
    fixtures, coordinates = ProductionTrainingService._fixtures_for_update(
        rng, replicate=3, update=17
    )
    assert coordinates == tuple((4, slot) for slot in range(6)) + tuple(
        (10, slot) for slot in range(6)
    )
    assert [fixture.regime for fixture in fixtures[:6]] == [Regime.FIXED_4] * 6
    assert [fixture.regime for fixture in fixtures[6:]] == [Regime.FIXED_10] * 6
    for half in (fixtures[:6], fixtures[6:]):
        assert sum(item.event_order is EventOrder.RG for item in half) == 3
        assert sum(item.event_order is EventOrder.GR for item in half) == 3
    repeated, repeated_coordinates = ProductionTrainingService._fixtures_for_update(
        rng, replicate=3, update=17
    )
    assert fixtures == repeated and coordinates == repeated_coordinates
    assert all(len(item.eta_v) == len(item.eta_omega) == 420 for item in fixtures)
    paired_uniform = rng.training_action_uniform(3, 17, 4, 2, 5)
    assert paired_uniform == rng.training_action_uniform(3, 17, 4, 2, 5)


def test_exact_reward_duration_records_and_twelve_terminal_slots_validate() -> None:
    records = tuple(
        TrainingRenewalRecord(
            k=4 if index < 6 else 10,
            slot=index % 6,
            renewal=0,
            action=index,
            realized_duration=1,
            primitive_rewards=(float(index) / 100.0,),
            terminal=True,
        )
        for index in range(12)
    )
    update = CollectedTrainingUpdate(
        observations=torch.zeros((12, 14), dtype=torch.float32),
        true_q=torch.tensor([0.0, 1.0] * 6, dtype=torch.float32),
        actions=torch.arange(12, dtype=torch.int64),
        primitive_rewards=tuple(record.primitive_rewards for record in records),
        nonterminal=torch.zeros(12, dtype=torch.bool),
        slot_offsets=tuple(range(13)),
        records=records,
    )
    update.validate()
    changed = list(records)
    changed[0] = TrainingRenewalRecord(4, 0, 0, 0, 2, (0.0,), True)
    with pytest.raises(ProductionTrainingError, match="primitive-duration"):
        CollectedTrainingUpdate(
            update.observations,
            update.true_q,
            update.actions,
            update.primitive_rewards,
            update.nonterminal,
            update.slot_offsets,
            tuple(changed),
        ).validate()


def test_blinded_frontier_file_tamper_is_rejected_before_restore(tmp_path) -> None:
    service = ProductionTrainingService(
        tmp_path / "result", bindings=_bindings(), run_identity=_run_identity()
    )
    permit, rng = _permit(), _rng()
    binding = service._binding_payload(permit, rng, 0, "TREAT")
    model_state = {"synthetic.weight": torch.tensor([0.25], dtype=torch.float32)}
    optimizer_state = {
        "arm": "TREAT",
        "step_index": 0,
        "parameter_names": ("synthetic.weight",),
        "first_moments": (torch.zeros(1, dtype=torch.float32),),
        "second_moments": (torch.zeros(1, dtype=torch.float32),),
        "law": {"synthetic": True},
    }
    payload = {
        "schema": _GENERATION_SCHEMA,
        "binding": binding,
        "generation": 0,
        "completed_update": 0,
        "optimizer_step": 0,
        "previous_generation_digest": None,
        "origin_lease_id": permit.lease_id,
        "update_record_digest": None,
        "checkpoint_digest": None,
        "complete_update": False,
        "partial_inspection_permitted": False,
        "scientific_endpoints_exposed": False,
        "model_state": model_state,
        "model_state_digest": _semantic_digest(model_state),
        "optimizer_state": optimizer_state,
        "optimizer_state_digest": _semantic_digest(optimizer_state),
    }
    generation = service._generation_path(0, "TREAT", 0)
    generation.parent.mkdir(parents=True)
    torch.save(payload, generation)
    digest = __import__("hashlib").sha256(generation.read_bytes()).hexdigest()
    service._write_pointer(
        replicate=0,
        arm="TREAT",
        generation=0,
        generation_digest=digest,
        binding=binding,
    )
    service._load_latest(permit, rng, 0, "TREAT")
    generation.write_bytes(generation.read_bytes() + b"tamper")
    with pytest.raises(ProductionTrainingError, match="file digest differs"):
        service._load_latest(permit, rng, 0, "TREAT")


def test_checkpoint_binding_tamper_is_rejected_without_model_materialization(tmp_path) -> None:
    service = ProductionTrainingService(
        tmp_path / "result", bindings=_bindings(), run_identity=_run_identity()
    )
    permit, rng = _permit(), _rng()
    binding = service._binding_payload(permit, rng, 2, "FREE")
    payload = {
        "schema": "SCDMP_UAV_SP_R02_FINAL_CHECKPOINT_V1",
        "binding": {**binding, "rng_identity_digest": "0" * 64},
        "generation": 144,
        "completed_update": 144,
        "optimizer_step": 2_304,
        "origin_lease_id": permit.lease_id,
        "partial_inspection_permitted": False,
        "scientific_endpoints_exposed": False,
        "model_state": {"synthetic": torch.zeros(1)},
        "optimizer_state": {"synthetic": torch.zeros(1)},
    }
    payload["model_state_digest"] = _semantic_digest(payload["model_state"])
    payload["optimizer_state_digest"] = _semantic_digest(payload["optimizer_state"])
    with pytest.raises(ProductionTrainingError, match="identity/binding"):
        service._validate_payload(
            payload,
            schema="SCDMP_UAV_SP_R02_FINAL_CHECKPOINT_V1",
            binding=binding,
            generation=144,
        )


def test_small_frontier_crash_reopen_new_lease_and_unaccepted_completion(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise the normal lifecycle with synthetic one-scalar dependencies."""

    class TinyModel:
        def __init__(self, arm: str, permit) -> None:
            self.arm = LearnedArm(arm)
            self.activity_permit = permit
            self.weight = torch.nn.Parameter(torch.tensor([0.25], dtype=torch.float32))

        def parameters(self):
            return iter((self.weight,))

        def state_dict(self):
            return {"weight": self.weight.detach().clone()}

        def load_state_dict(self, state, strict=True):
            if strict and set(state) != {"weight"}:
                raise ValueError("tiny state mismatch")
            with torch.no_grad():
                self.weight.copy_(state["weight"])

        def eval(self):
            return self

    class TinyOptimizer:
        def __init__(self, model, *, permit) -> None:
            self.arm = model.arm
            self.model = model
            self.step_index = 0

        def state_dict(self):
            return {
                "arm": self.arm.value,
                "step_index": self.step_index,
                "moment": torch.tensor([float(self.step_index)], dtype=torch.float32),
            }

        def load_state_dict(self, state):
            if state["arm"] != self.arm.value:
                raise ValueError("tiny optimizer arm mismatch")
            self.step_index = int(state["step_index"])

    crash_update_two = {"enabled": True}

    class TinyTrainer:
        def __init__(self, model, *, permit, optimizer) -> None:
            self.model = model
            self.optimizer = optimizer

        def train_update(self, batch, *, replicate, update, permutations):
            if update == 2 and crash_update_two["enabled"]:
                raise RuntimeError("synthetic crash before second update mutation")
            with torch.no_grad():
                self.model.weight.add_(float(update))
            self.optimizer.step_index += 16
            return tuple(range(16))

    def tiny_build_model(arm, *, permit, replicate, initialization_source):
        permit.require_model_initialization(
            card_revision=CARD_REVISION,
            replicate=replicate,
            arm=LearnedArm(arm).value,
            initialization_source=initialization_source,
        )
        return TinyModel(LearnedArm(arm).value, permit)

    records = tuple(
        TrainingRenewalRecord(
            k=4 if index < 6 else 10,
            slot=index % 6,
            renewal=0,
            action=index,
            realized_duration=1,
            primitive_rewards=(0.01 * index,),
            terminal=True,
        )
        for index in range(12)
    )
    collected = CollectedTrainingUpdate(
        observations=torch.zeros((12, 14), dtype=torch.float32),
        true_q=torch.tensor([0.0, 1.0] * 6, dtype=torch.float32),
        actions=torch.arange(12, dtype=torch.int64),
        primitive_rewards=tuple(item.primitive_rewards for item in records),
        nonterminal=torch.zeros(12, dtype=torch.bool),
        slot_offsets=tuple(range(13)),
        records=records,
    )
    collected.validate()

    monkeypatch.setattr(production_module, "_UPDATES", 2)
    monkeypatch.setattr(production_module, "MAX_OPTIMIZER_STEP", 32)
    monkeypatch.setattr(production_module, "build_model", tiny_build_model)
    monkeypatch.setattr(production_module, "ExactAdamW", TinyOptimizer)
    monkeypatch.setattr(production_module, "DurationCorrectPPOTrainer", TinyTrainer)
    monkeypatch.setattr(production_module, "freeze_update_batch", lambda *args, **kwargs: object())
    monkeypatch.setattr(
        ProductionTrainingService,
        "_collect_update",
        lambda self, model, rng, *, replicate, update: collected,
    )

    bindings = _bindings()
    run_identity = _run_identity(bindings)
    root = tmp_path / "synthetic-lifecycle"
    first_permit = _permit()
    first_rng = EmpiricalRNG(bytes(range(32)), first_permit)
    first = ProductionTrainingService(
        root, bindings=bindings, run_identity=run_identity
    )
    frontier = first.create_frontier(first_permit, first_rng, 0, "TREAT")
    with pytest.raises(RuntimeError, match="synthetic crash"):
        first.train_slot(first_permit, first_rng, frontier)
    pointer = json.loads((root / "training/replicate-00/TREAT/frontier.json").read_text())
    assert pointer["generation"] == 1

    second_permit = ActivityPermit(
        lease_id="SYNTHETIC-CONTINUATION-LEASE",
        coordinate_plan_digest=COORDINATE_PLAN_DIGEST,
        workers=1,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        _validation_seal=lease_module._PERMIT_SEAL,
    )
    second_rng = EmpiricalRNG(bytes(range(32)), second_permit)
    reopened = ProductionTrainingService(
        root, bindings=bindings, run_identity=run_identity
    )
    resumed_frontier = reopened.create_frontier(
        second_permit, second_rng, 0, "TREAT"
    )
    crash_update_two["enabled"] = False
    completion = reopened.train_slot(second_permit, second_rng, resumed_frontier)
    completion.validate_completion()
    assert completion.technically_accepted is False
    assert completion.origin_lease_id == first_permit.lease_id
    assert completion.run_identity_digest == run_identity.run_identity_digest
    assert completion.optimizer_step == 32
    assert __import__("pathlib").Path(completion.checkpoint_path).is_file()

    changed_master_identity = TrainingRunIdentity.create(
        master_digest="4" * 64, bindings=bindings
    )
    changed_master = ProductionTrainingService(
        root, bindings=bindings, run_identity=changed_master_identity
    )
    with pytest.raises(ProductionTrainingError, match="pointer binding differs"):
        changed_master.create_frontier(second_permit, second_rng, 0, "TREAT")

    changed_source = TrainingSourceBindings(
        CARD_REVISION, SCIENCE_CARD_SHA256, "9" * 64, "2" * 64
    )
    changed_source_service = ProductionTrainingService(
        root,
        bindings=changed_source,
        run_identity=_run_identity(changed_source),
    )
    with pytest.raises(ProductionTrainingError, match="pointer binding differs"):
        changed_source_service.create_frontier(second_permit, second_rng, 0, "TREAT")

    changed_coordinate_permit = ActivityPermit(
        lease_id="CHANGED-COORDINATE-LEASE",
        coordinate_plan_digest="f" * 64,
        workers=1,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        _validation_seal=lease_module._PERMIT_SEAL,
    )
    with pytest.raises(ProductionTrainingError, match="coordinate differs"):
        reopened.create_frontier(
            changed_coordinate_permit, second_rng, 0, "TREAT"
        )


def test_evaluation_loader_rejects_unaccepted_checkpoint_receipt(tmp_path) -> None:
    service = ProductionTrainingService(
        tmp_path / "result", bindings=_bindings(), run_identity=_run_identity()
    )
    unaccepted = CheckpointReceipt(
        replicate=0,
        arm="TREAT",
        coordinate_digest=COORDINATE_PLAN_DIGEST,
        checkpoint_digest="a" * 64,
        optimizer_step=2_304,
        technically_accepted=False,
    )
    with pytest.raises(FrontierContractError, match="lacks technical acceptance"):
        service.load_final_model(
            permit=_permit(),
            rng=_rng(),
            replicate=0,
            arm="TREAT",
            checkpoint_receipt=unaccepted,
        )


def test_cm_completion_validator_authenticates_payload_checkpoint_and_full_chain(
    tmp_path,
) -> None:
    """Use tiny tensor payloads; no model, host, rollout, or endpoint is loaded."""

    bindings = _bindings()
    run_identity = _run_identity(bindings)
    root = (tmp_path / "cm-validation").resolve()
    permit = ActivityPermit(
        lease_id="SYNTHETIC-CM-VALIDATION-LEASE",
        coordinate_plan_digest=COORDINATE_PLAN_DIGEST,
        workers=1,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        phase="TRAIN",
        source_manifest_sha256=bindings.empirical_source_manifest_sha256,
        native_binding_digest=bindings.native_binding_digest,
        card_sha256=bindings.card_sha256,
        _validation_seal=lease_module._PERMIT_SEAL,
    )
    rng = EmpiricalRNG(bytes(range(32)), permit)
    service = ProductionTrainingService(
        root, bindings=bindings, run_identity=run_identity
    )
    binding = service._binding_payload(permit, rng, 0, "TREAT")
    origin_lease_id = "ORIGINAL-SYNTHETIC-TRAIN-LEASE"

    def state(generation: int):
        model = {"synthetic.weight": torch.tensor([float(generation)], dtype=torch.float32)}
        optimizer = {
            "arm": "TREAT",
            "step_index": generation * 16,
            "synthetic.moment": torch.tensor([float(generation)], dtype=torch.float32),
        }
        return model, optimizer

    final_model, final_optimizer = state(144)
    checkpoint_payload = {
        "schema": "SCDMP_UAV_SP_R02_FINAL_CHECKPOINT_V1",
        "binding": binding,
        "generation": 144,
        "completed_update": 144,
        "optimizer_step": 2_304,
        "origin_lease_id": origin_lease_id,
        "partial_inspection_permitted": False,
        "scientific_endpoints_exposed": False,
        "model_state": final_model,
        "model_state_digest": _semantic_digest(final_model),
        "optimizer_state": final_optimizer,
        "optimizer_state_digest": _semantic_digest(final_optimizer),
    }
    checkpoint_path = service._checkpoint_path(0, "TREAT")
    checkpoint_digest = production_module._atomic_create_torch(
        checkpoint_path, checkpoint_payload
    )

    previous: str | None = None
    final_generation_digest = ""
    for generation in range(145):
        model_state, optimizer_state = state(generation)
        payload = {
            "schema": _GENERATION_SCHEMA,
            "binding": binding,
            "generation": generation,
            "completed_update": generation,
            "optimizer_step": generation * 16,
            "previous_generation_digest": previous,
            "origin_lease_id": origin_lease_id,
            "update_record_digest": None if generation == 0 else f"{generation:064x}",
            "checkpoint_digest": checkpoint_digest if generation == 144 else None,
            "complete_update": generation > 0,
            "partial_inspection_permitted": False,
            "scientific_endpoints_exposed": False,
            "model_state": model_state,
            "model_state_digest": _semantic_digest(model_state),
            "optimizer_state": optimizer_state,
            "optimizer_state_digest": _semantic_digest(optimizer_state),
        }
        final_generation_digest = production_module._atomic_create_torch(
            service._generation_path(0, "TREAT", generation), payload
        )
        previous = final_generation_digest
    service._write_pointer(
        replicate=0,
        arm="TREAT",
        generation=144,
        generation_digest=final_generation_digest,
        binding=binding,
    )

    runner_identity_digest = "7" * 64
    completion_path = (
        root / "checkpoint-completions/replicate-00-TREAT.json"
    ).resolve()
    completion_payload = {
        "schema": "SCDMP_UAV_SP_R02_CHECKPOINT_COMPLETION_V1",
        "replicate": 0,
        "arm": "TREAT",
        "coordinate_digest": COORDINATE_PLAN_DIGEST,
        "run_identity_digest": runner_identity_digest,
        "checkpoint_path": str(checkpoint_path.resolve()),
        "checkpoint_digest": checkpoint_digest,
        "optimizer_step": 2_304,
        "origin_lease_id": origin_lease_id,
        "empirical_source_manifest_sha256": bindings.empirical_source_manifest_sha256,
        "card_revision": bindings.card_revision,
        "card_sha256": bindings.card_sha256,
        "native_binding_digest": bindings.native_binding_digest,
        "technically_accepted": False,
        "evaluation_observed": False,
    }
    encoded = json.dumps(
        completion_payload, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")
    completion_path.parent.mkdir(parents=True)
    completion_path.write_bytes(encoded)
    completion = CheckpointCompletion(
        replicate=0,
        arm="TREAT",
        coordinate_digest=COORDINATE_PLAN_DIGEST,
        run_identity_digest=runner_identity_digest,
        checkpoint_path=str(checkpoint_path.resolve()),
        checkpoint_digest=checkpoint_digest,
        completion_payload_path=str(completion_path),
        completion_payload_digest=__import__("hashlib").sha256(encoded).hexdigest(),
        optimizer_step=2_304,
        technically_accepted=False,
        evaluation_observed=False,
    )
    validator = service.checkpoint_completion_validator(
        permit=permit,
        rng=rng,
        run_identity_digest=runner_identity_digest,
    )
    assert validator(completion) is None

    self_accepted = __import__("dataclasses").replace(
        completion, technically_accepted=True
    )
    with pytest.raises(FrontierContractError, match="cannot self-accept"):
        validator(self_accepted)
    changed_runner = __import__("dataclasses").replace(
        completion, run_identity_digest="8" * 64
    )
    with pytest.raises(ProductionTrainingError, match="runner identity differs"):
        validator(changed_runner)

    changed_source_permit = ActivityPermit(
        lease_id="CHANGED-SOURCE-CM-LEASE",
        coordinate_plan_digest=COORDINATE_PLAN_DIGEST,
        workers=1,
        expires_at=permit.expires_at,
        source_manifest_sha256="9" * 64,
        native_binding_digest=bindings.native_binding_digest,
        card_sha256=bindings.card_sha256,
        _validation_seal=lease_module._PERMIT_SEAL,
    )
    changed_source_validator = service.checkpoint_completion_validator(
        permit=changed_source_permit,
        rng=rng,
        run_identity_digest=runner_identity_digest,
    )
    with pytest.raises(ProductionTrainingError, match="source manifest differs"):
        changed_source_validator(completion)
