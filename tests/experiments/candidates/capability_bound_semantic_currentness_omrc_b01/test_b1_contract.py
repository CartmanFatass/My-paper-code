from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import b1_contract


def test_b1_plan_freezes_exact_three_seed_exposure_and_caps() -> None:
    plan = b1_contract.B1Plan()

    assert plan.run_name == "CBSC-OMRC-B1-THREE-SEED-SCOUT"
    assert plan.seeds == (21101, 21121, 21143)
    assert plan.arms == (
        "STRUCT-CURRENTNESS-GRU",
        "RAW-GRU",
        "PI-GRU",
        "DERANGED-CURRENTNESS-GRU",
    )
    assert plan.train_episode_ids == tuple(range(384))
    assert plan.rollout_updates == 48
    assert plan.ppo_epochs == 4
    assert plan.minibatches_per_epoch == 4
    assert plan.minibatch_episode_count == 2
    assert plan.optimizer_steps_per_arm_seed == 768
    assert plan.checkpoint_updates == (0, 12, 24, 48)
    assert plan.eval_stochastic_ids == tuple(range(32))
    assert plan.eval_motif_ids == tuple(range(32))
    assert plan.counts_per_arm_seed == {
        "train_episodes": 384,
        "train_transitions": 58_368,
        "train_decisions": 9_216,
        "rollout_updates": 48,
        "ppo_epochs_per_rollout": 4,
        "minibatches_per_epoch": 4,
        "optimizer_steps": 768,
        "checkpoint_count": 4,
        "evaluation_episodes_per_checkpoint": 64,
        "evaluation_transitions_per_checkpoint": 9_728,
        "evaluation_decisions_per_checkpoint": 1_536,
        "evaluation_episodes": 256,
        "evaluation_transitions": 38_912,
        "evaluation_decisions": 6_144,
    }
    assert plan.resource_caps.as_dict() == {
        "wall_seconds": 7_200.0,
        "process_tree_peak_rss_bytes": 4 * 1024**3,
        "scratch_high_water_bytes": 2 * 1024**3,
        "durable_high_water_bytes": 512 * 1024**2,
    }
    assert plan.object_durable_cap_bytes == 512 * 1024**2
    assert plan.object_id == "CBSC-OMRC-B01"
    assert plan.innovator_selection_request_id == "cbsc-online-b-innovator-20260901-01"
    assert plan.innovator_selection_response_sha256 == (
        "94f163f8ba777950c9c19ffac1acca3c697f09642d4713ef13b1e66d9f04d778"
    )
    assert plan.innovator_selection_archive_path.endswith(
        "cbsc-online-b-innovator-20260901-01/RESPONSE.md"
    )
    assert plan.literal_binding_request_id == "cbsc-online-b-innovator-20260901-02"
    assert plan.literal_binding_response_sha256 == (
        "e96df981f7cdb40a6206f2fddcc989a05783491a1fa422e7b0ca673344a05844"
    )
    assert plan.metrics_only_request_id == "cbsc-online-b-innovator-20260901-03"
    assert plan.metrics_only_response_sha256 == (
        "7a3bd74e12508e22ea577a1563737eda119c10560e094b25279503648d1105f7"
    )
    assert plan.scientific_branch is None

    with pytest.raises(FrozenInstanceError):
        plan.seeds = (1,)  # type: ignore[misc]
    with pytest.raises(b1_contract.B1ContractError):
        b1_contract.B1Plan(seeds=(21101,))
    with pytest.raises(b1_contract.B1ContractError):
        b1_contract.B1Plan(
            innovator_selection_response_sha256="0" * 64
        )


def _request(tmp_path: Path, **changes: object) -> b1_contract.B1ArmSeedRequest:
    values: dict[str, object] = {
        "plan": b1_contract.B1Plan(),
        "attempt_id": "b1-attempt-01",
        "arm": "STRUCT-CURRENTNESS-GRU",
        "seed": 21101,
        "train_episode_ids": tuple(range(384)),
        "checkpoint_updates": (0, 12, 24, 48),
        "eval_stochastic_ids": tuple(range(32)),
        "eval_motif_ids": tuple(range(32)),
        "scratch_root": tmp_path / "scratch",
        "durable_root": tmp_path / "durable",
        "admission_schema": "cbsc_omrc_b01_b1_bound_admission_v1",
        "admission_receipt_path": tmp_path / "admission.json",
        "admission_receipt_sha256": "1" * 64,
        "implementation_commit": "a" * 40,
        "source_conformance_sha256": "b" * 64,
        "resource_caps": b1_contract.B1_RESOURCE_CAPS,
        "scientific_branch": None,
    }
    values.update(changes)
    return b1_contract.B1ArmSeedRequest(**values)  # type: ignore[arg-type]


def test_arm_seed_request_is_exact_immutable_and_binds_admission_identity(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)

    assert request.plan == b1_contract.B1Plan()
    assert request.run_name == "CBSC-OMRC-B1-THREE-SEED-SCOUT"
    assert request.arm == "STRUCT-CURRENTNESS-GRU" and request.seed == 21101
    assert request.train_episode_ids == tuple(range(384))
    assert request.checkpoint_updates == (0, 12, 24, 48)
    assert request.eval_stochastic_ids == tuple(range(32))
    assert request.eval_motif_ids == tuple(range(32))
    assert request.scratch_root.is_absolute()
    assert request.durable_root.is_absolute()
    assert request.admission_receipt_path.is_absolute()
    assert request.admission_binding == {
        "schema": "cbsc_omrc_b01_b1_bound_admission_v1",
        "attempt_id": "b1-attempt-01",
        "run_name": "CBSC-OMRC-B1-THREE-SEED-SCOUT",
        "arm": "STRUCT-CURRENTNESS-GRU",
        "seed": 21101,
        "implementation_commit": "a" * 40,
        "source_conformance_sha256": "b" * 64,
        "bound_receipt_path": str((tmp_path / "admission.json").resolve()),
        "bound_receipt_sha256": "1" * 64,
    }
    assert request.resource_caps.wall_seconds == 7_200.0
    assert request.scientific_branch is None

    with pytest.raises(FrozenInstanceError):
        request.seed = 21121  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field", "changed"),
    (
        ("attempt_id", ""),
        ("arm", "UNKNOWN"),
        ("seed", 21001),
        ("seed", True),
        ("train_episode_ids", list(range(384))),
        ("checkpoint_updates", (0, 12, 48)),
        ("eval_stochastic_ids", tuple(range(31))),
        ("eval_motif_ids", tuple(range(1, 33))),
        ("scratch_root", Path("relative-scratch")),
        ("durable_root", Path("relative-durable")),
        ("admission_schema", "wrong"),
        ("admission_receipt_path", Path("relative-receipt.json")),
        ("admission_receipt_sha256", "1" * 63),
        ("implementation_commit", "A" * 40),
        ("source_conformance_sha256", "b" * 63),
        (
            "resource_caps",
            b1_contract.ResourceCaps(wall_seconds=7_199.0),
        ),
        ("scientific_branch", "PRELIMINARY_SEMANTIC_CURRENTNESS_SIGNAL"),
    ),
)
def test_arm_seed_request_rejects_type_identity_path_and_exposure_drift(
    tmp_path: Path, field: str, changed: object
) -> None:
    with pytest.raises(b1_contract.B1ContractError):
        _request(tmp_path, **{field: changed})


def _ledger_binding(**changes: object) -> b1_contract.B1LedgerBinding:
    values: dict[str, object] = {
        "attempt_id": "b1-attempt-ledger-01",
        "run_name": "CBSC-OMRC-B1-THREE-SEED-SCOUT",
        "implementation_commit": "a" * 40,
        "source_conformance_sha256": "b" * 64,
        "configuration_sha256": "c" * 64,
        "laws_sha256": "d" * 64,
        "b0_manifest_sha256": "e" * 64,
        "b0_manifest_bytes": 12_807_274,
        "b0_reviewed_receipt_sha256": "9" * 64,
        "b0_inventory_sha256": "184fa6ad3c915d728892923e7b99840c8faba95fe78647f869f81ecf2fb4f9c5",
        "b0_file_count": 33,
        "b0_total_bytes": 12_807_274,
        "object_id": "CBSC-OMRC-B01",
        "innovator_selection_request_id": "cbsc-online-b-innovator-20260901-01",
        "innovator_selection_archive_path": (
            "temp/sessions/hmasd-chatgpt-pro-transport/archive/"
            "capability_bound_semantic_currentness/"
            "cbsc-online-b-innovator-20260901-01/RESPONSE.md"
        ),
        "innovator_selection_response_sha256": (
            "94f163f8ba777950c9c19ffac1acca3c697f09642d4713ef13b1e66d9f04d778"
        ),
        "literal_binding_request_id": "cbsc-online-b-innovator-20260901-02",
        "literal_binding_archive_path": (
            "temp/sessions/hmasd-chatgpt-pro-transport/archive/"
            "capability_bound_semantic_currentness/"
            "cbsc-online-b-innovator-20260901-02/RESPONSE.md"
        ),
        "literal_binding_response_sha256": (
            "e96df981f7cdb40a6206f2fddcc989a05783491a1fa422e7b0ca673344a05844"
        ),
        "metrics_only_request_id": "cbsc-online-b-innovator-20260901-03",
        "metrics_only_archive_path": (
            "temp/sessions/hmasd-chatgpt-pro-transport/archive/"
            "capability_bound_semantic_currentness/"
            "cbsc-online-b-innovator-20260901-03/RESPONSE.md"
        ),
        "metrics_only_response_sha256": (
            "7a3bd74e12508e22ea577a1563737eda119c10560e094b25279503648d1105f7"
        ),
    }
    values.update(changes)
    return b1_contract.B1LedgerBinding(**values)  # type: ignore[arg-type]


def _pending_slots(
    binding: b1_contract.B1LedgerBinding,
) -> tuple[b1_contract.B1SlotLedgerEntry, ...]:
    return tuple(
        b1_contract.B1SlotLedgerEntry(
            binding=binding,
            slot_index=index,
            seed=seed,
            arm=arm,
            status=b1_contract.B1SlotStatus.PENDING,
        )
        for index, (seed, arm) in enumerate(b1_contract.B1_SLOT_ORDER)
    )


def _attempt_ledger(
    slots: tuple[b1_contract.B1SlotLedgerEntry, ...] | None = None,
) -> b1_contract.B1AttemptLedger:
    binding = _ledger_binding() if slots is None else slots[0].binding
    return b1_contract.B1AttemptLedger(
        schema="cbsc_omrc_b01_b1_attempt_incident_ledger_v1",
        publication_mode="CREATE_ONLY",
        binding=binding,
        slots=_pending_slots(binding) if slots is None else slots,
    )


def test_attempt_ledger_freezes_create_only_seed_major_twelve_slot_schema() -> None:
    assert b1_contract.B1_SLOT_ORDER == (
        (21101, "STRUCT-CURRENTNESS-GRU"),
        (21101, "RAW-GRU"),
        (21101, "PI-GRU"),
        (21101, "DERANGED-CURRENTNESS-GRU"),
        (21121, "STRUCT-CURRENTNESS-GRU"),
        (21121, "RAW-GRU"),
        (21121, "PI-GRU"),
        (21121, "DERANGED-CURRENTNESS-GRU"),
        (21143, "STRUCT-CURRENTNESS-GRU"),
        (21143, "RAW-GRU"),
        (21143, "PI-GRU"),
        (21143, "DERANGED-CURRENTNESS-GRU"),
    )
    ledger = _attempt_ledger()
    assert b1_contract.validate_b1_attempt_ledger(ledger) is ledger
    assert tuple(slot.status.value for slot in ledger.slots) == ("PENDING",) * 12
    assert ledger.binding.as_dict() == {
        "attempt_id": "b1-attempt-ledger-01",
        "run_name": "CBSC-OMRC-B1-THREE-SEED-SCOUT",
        "implementation_commit": "a" * 40,
        "source_conformance_sha256": "b" * 64,
        "configuration_sha256": "c" * 64,
        "laws_sha256": "d" * 64,
        "b0_manifest_sha256": "e" * 64,
        "b0_manifest_bytes": 12_807_274,
        "b0_reviewed_receipt_sha256": "9" * 64,
        "b0_inventory_sha256": "184fa6ad3c915d728892923e7b99840c8faba95fe78647f869f81ecf2fb4f9c5",
        "b0_file_count": 33,
        "b0_total_bytes": 12_807_274,
        "object_id": "CBSC-OMRC-B01",
        "innovator_selection_request_id": "cbsc-online-b-innovator-20260901-01",
        "innovator_selection_archive_path": (
            "temp/sessions/hmasd-chatgpt-pro-transport/archive/"
            "capability_bound_semantic_currentness/"
            "cbsc-online-b-innovator-20260901-01/RESPONSE.md"
        ),
        "innovator_selection_response_sha256": (
            "94f163f8ba777950c9c19ffac1acca3c697f09642d4713ef13b1e66d9f04d778"
        ),
        "literal_binding_request_id": "cbsc-online-b-innovator-20260901-02",
        "literal_binding_archive_path": (
            "temp/sessions/hmasd-chatgpt-pro-transport/archive/"
            "capability_bound_semantic_currentness/"
            "cbsc-online-b-innovator-20260901-02/RESPONSE.md"
        ),
        "literal_binding_response_sha256": (
            "e96df981f7cdb40a6206f2fddcc989a05783491a1fa422e7b0ca673344a05844"
        ),
        "metrics_only_request_id": "cbsc-online-b-innovator-20260901-03",
        "metrics_only_archive_path": (
            "temp/sessions/hmasd-chatgpt-pro-transport/archive/"
            "capability_bound_semantic_currentness/"
            "cbsc-online-b-innovator-20260901-03/RESPONSE.md"
        ),
        "metrics_only_response_sha256": (
            "7a3bd74e12508e22ea577a1563737eda119c10560e094b25279503648d1105f7"
        ),
    }
    with pytest.raises(FrozenInstanceError):
        ledger.schema = "changed"  # type: ignore[misc]


def test_complete_slot_requires_all_four_evidence_digests() -> None:
    binding = _ledger_binding()
    complete = b1_contract.B1SlotLedgerEntry(
        binding=binding,
        slot_index=0,
        seed=21101,
        arm="STRUCT-CURRENTNESS-GRU",
        status=b1_contract.B1SlotStatus.COMPLETE,
        raw_result_sha256="1" * 64,
        admission_sha256="2" * 64,
        telemetry_sha256="3" * 64,
        files_sha256="4" * 64,
    )
    slots = (complete, *_pending_slots(binding)[1:])
    assert _attempt_ledger(slots).slots[0].status is b1_contract.B1SlotStatus.COMPLETE

    for field in (
        "raw_result_sha256",
        "admission_sha256",
        "telemetry_sha256",
        "files_sha256",
    ):
        values = {
            "raw_result_sha256": "1" * 64,
            "admission_sha256": "2" * 64,
            "telemetry_sha256": "3" * 64,
            "files_sha256": "4" * 64,
        }
        values[field] = None
        with pytest.raises(b1_contract.B1ContractError, match="COMPLETE"):
            b1_contract.B1SlotLedgerEntry(
                binding=binding,
                slot_index=0,
                seed=21101,
                arm="STRUCT-CURRENTNESS-GRU",
                status=b1_contract.B1SlotStatus.COMPLETE,
                **values,
            )


def _incomplete_slot(
    binding: b1_contract.B1LedgerBinding,
    *,
    slot_index: int = 0,
    update: int = 12,
    resume_binding: b1_contract.B1LedgerBinding | None = None,
) -> b1_contract.B1SlotLedgerEntry:
    seed, arm = b1_contract.B1_SLOT_ORDER[slot_index]
    resume = b1_contract.B1ResumeCheckpointBinding(
        binding=binding if resume_binding is None else resume_binding,
        slot_index=slot_index,
        seed=seed,
        arm=arm,
        completed_rollout_updates=update,
        checkpoint_relative_path=f"slots/{slot_index:02d}/checkpoint-update-{update}.pt",
        checkpoint_sha256="5" * 64,
        order_chain_sha256="6" * 64,
    )
    return b1_contract.B1SlotLedgerEntry(
        binding=binding,
        slot_index=slot_index,
        seed=seed,
        arm=arm,
        status=b1_contract.B1SlotStatus.INCOMPLETE,
        incident_sha256="7" * 64,
        resume_checkpoint=resume,
    )


def test_incomplete_slot_requires_bound_nonbare_resumable_checkpoint() -> None:
    binding = _ledger_binding()
    incomplete = _incomplete_slot(binding)
    ledger = _attempt_ledger((incomplete, *_pending_slots(binding)[1:]))
    assert ledger.slots[0].resume_checkpoint.completed_rollout_updates == 12

    with pytest.raises(b1_contract.B1ContractError, match="resume checkpoint"):
        b1_contract.B1SlotLedgerEntry(
            binding=binding,
            slot_index=0,
            seed=21101,
            arm="STRUCT-CURRENTNESS-GRU",
            status=b1_contract.B1SlotStatus.INCOMPLETE,
            incident_sha256="7" * 64,
            resume_checkpoint=Path("checkpoint-update-12.pt"),  # type: ignore[arg-type]
        )
    with pytest.raises(b1_contract.B1ContractError, match="boundary"):
        _incomplete_slot(binding, update=48)
    with pytest.raises(b1_contract.B1ContractError, match="binding"):
        _incomplete_slot(
            binding,
            resume_binding=_ledger_binding(source_conformance_sha256="8" * 64),
        )


def test_precheckpoint_incomplete_slot_preserves_incident_and_restarts_fresh() -> None:
    binding = _ledger_binding()
    incomplete = b1_contract.B1SlotLedgerEntry(
        binding=binding,
        slot_index=0,
        seed=21101,
        arm="STRUCT-CURRENTNESS-GRU",
        status=b1_contract.B1SlotStatus.INCOMPLETE,
        incident_sha256="7" * 64,
        resume_checkpoint=None,
    )
    ledger = _attempt_ledger((incomplete, *_pending_slots(binding)[1:]))
    assert ledger.slots[0].resume_checkpoint is None


def test_ledger_rejects_second_incomplete_reordering_and_cross_source_mix() -> None:
    binding = _ledger_binding()
    pending = _pending_slots(binding)
    with pytest.raises(b1_contract.B1ContractError, match="at most one INCOMPLETE"):
        _attempt_ledger(
            (_incomplete_slot(binding, slot_index=0), _incomplete_slot(binding, slot_index=1), *pending[2:])
        )
    with pytest.raises(b1_contract.B1ContractError, match="seed-major"):
        _attempt_ledger((pending[1], pending[0], *pending[2:]))

    other = _ledger_binding(source_conformance_sha256="8" * 64)
    mixed = b1_contract.B1SlotLedgerEntry(
        binding=other,
        slot_index=0,
        seed=21101,
        arm="STRUCT-CURRENTNESS-GRU",
        status=b1_contract.B1SlotStatus.PENDING,
    )
    with pytest.raises(b1_contract.B1ContractError, match="cross-source"):
        _attempt_ledger((mixed, *pending[1:]))


def test_ledger_statuses_form_complete_incomplete_pending_prefix_order() -> None:
    binding = _ledger_binding()
    pending = _pending_slots(binding)
    complete_slot_one = b1_contract.B1SlotLedgerEntry(
        binding=binding,
        slot_index=1,
        seed=21101,
        arm="RAW-GRU",
        status=b1_contract.B1SlotStatus.COMPLETE,
        raw_result_sha256="1" * 64,
        admission_sha256="2" * 64,
        telemetry_sha256="3" * 64,
        files_sha256="4" * 64,
    )
    with pytest.raises(b1_contract.B1ContractError, match="status progression"):
        _attempt_ledger((pending[0], complete_slot_one, *pending[2:]))


@pytest.mark.parametrize(
    ("field", "changed"),
    (
        ("b0_manifest_sha256", "e" * 63),
        ("b0_manifest_sha256", "E" * 64),
        ("b0_manifest_bytes", 0),
        ("b0_manifest_bytes", True),
        ("b0_reviewed_receipt_sha256", "9" * 63),
        ("b0_reviewed_receipt_sha256", "G" * 64),
        ("b0_inventory_sha256", "1" * 63),
        ("b0_inventory_sha256", "Z" * 64),
        ("b0_file_count", 0),
        ("b0_file_count", True),
        ("b0_total_bytes", 0),
        ("b0_total_bytes", True),
    ),
)
def test_ledger_binding_rejects_invalid_result_blind_b0_identity(
    field: str, changed: object
) -> None:
    with pytest.raises(b1_contract.B1ContractError):
        _ledger_binding(**{field: changed})


@pytest.mark.parametrize(
    ("field", "changed"),
    (
        ("object_id", "CBSC-OMRC-B00"),
        ("innovator_selection_request_id", "cbsc-online-b-innovator-20260901-02"),
        ("innovator_selection_archive_path", "unbound/RESPONSE.md"),
        ("innovator_selection_response_sha256", "0" * 64),
        ("literal_binding_request_id", "cbsc-online-b-innovator-20260901-01"),
        ("literal_binding_response_sha256", "0" * 64),
        ("metrics_only_request_id", "cbsc-online-b-innovator-20260901-02"),
        ("metrics_only_response_sha256", "0" * 64),
    ),
)
def test_ledger_binding_rejects_scientific_authority_drift(
    field: str, changed: object
) -> None:
    with pytest.raises(b1_contract.B1ContractError, match="frozen B1 contract"):
        _ledger_binding(**{field: changed})


def test_resume_checkpoint_refuses_cross_b0_manifest_mix() -> None:
    binding = _ledger_binding()
    other_b0 = _ledger_binding(b0_manifest_sha256="f" * 64)
    with pytest.raises(b1_contract.B1ContractError, match="binding"):
        _incomplete_slot(binding, resume_binding=other_b0)
    other_review = _ledger_binding(b0_reviewed_receipt_sha256="8" * 64)
    with pytest.raises(b1_contract.B1ContractError, match="binding"):
        _incomplete_slot(binding, resume_binding=other_review)
    other_inventory = _ledger_binding(b0_inventory_sha256="7" * 64)
    with pytest.raises(b1_contract.B1ContractError, match="binding"):
        _incomplete_slot(binding, resume_binding=other_inventory)
