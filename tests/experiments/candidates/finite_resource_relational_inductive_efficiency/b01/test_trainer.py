from __future__ import annotations

import dataclasses
import json
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.arms import initialize_paired_arms
from experiments.candidates.finite_resource_relational_inductive_efficiency.policy import FRRIEActorCritic, TORCH_AVAILABLE
from experiments.candidates.finite_resource_relational_inductive_efficiency.rng import AddressedRNG
from experiments.candidates.finite_resource_relational_inductive_efficiency.state_codec import (
    decode_optimizer_state, encode_optimizer_state,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.training import (
    LossReductionReceipt, RSCFEpisode, validate_loss_reduction_receipt, make_optimizer,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts.core import (
    ContractError,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.tapes import generate_episode_tape
from experiments.candidates.finite_resource_relational_inductive_efficiency.policy import LEGAL_ACTION_INDICES
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import B01ContractError, validate_resource_receipt
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.native_batch import BatchWorkLedger, _LEDGER_TOKEN
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.trainer import (
    ArmUpdateReceipt, B01ArmBatch, PairedB01Trainer, ProjectionObservedTrainer,
    assert_common_exogenous_and_work, assert_precontact_observation_equality,
    assert_paired_episode_information, capture_exogenous_episode,
)

pytestmark = pytest.mark.skipif(not TORCH_AVAILABLE, reason="Torch is required")


def _admit(tmp_path: Path) -> None:
    receipt = (tmp_path / "trainer-admit-memory.json").resolve()
    completed = subprocess.run(
        [sys.executable, str(Path("scripts/hmasd_resource_preflight.py").resolve()),
         "admit-memory", "--out", str(receipt)],
        check=False, capture_output=True, text=True, timeout=30,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    validate_resource_receipt(json.loads(receipt.read_text(encoding="utf-8")))


def _models():
    phy, edge = initialize_paired_arms(AddressedRNG(b"T" * 32), "FRRIE-TEST-ONLY-B01-TRAINER")
    models = {"PHY_TRUST": FRRIEActorCritic(phy), "EDGE_FLEX": FRRIEActorCritic(edge)}
    return models, {arm: make_optimizer(model) for arm, model in models.items()}


def _episode(torch, roster: int, model) -> RSCFEpisode:
    roles = torch.arange(roster, dtype=torch.int64) % 3
    observations = torch.linspace(-0.5, 0.5, roster * 22, dtype=torch.float32).reshape(roster, 22)
    actor = model.actor_step(observations, roles, model.initial_hidden(roster))
    selected = actor.probabilities.index_select(0, torch.tensor((0, 1, 2)))
    legal = torch.tensor(
        ((1, 1, 0, 0, 0, 1), (1, 1, 0, 0, 0, 1), (0, 0, 1, 1, 1, 1)),
        dtype=torch.bool,
    )
    q_targets = torch.full((3, 6), float("nan"), dtype=torch.float32)
    q_targets[legal] = 0.0
    return RSCFEpisode(
        roster_size=roster, selected_probabilities=selected,
        q_targets=q_targets, legal_masks=legal,
        factual_actions=torch.tensor((0, 1, 2), dtype=torch.int64),
        all_probabilities=actor.probabilities.unsqueeze(0).expand(12, -1, -1),
        critic_values=model.critic_values(observations.unsqueeze(0).expand(12, -1, -1), roles),
        terminal_return=torch.tensor(0.5, dtype=torch.float32),
    )


def _episodes(model):
    import torch
    by_roster = {roster: _episode(torch, roster, model) for roster in (9, 15)}
    return tuple(
        dataclasses.replace(by_roster[9 if position % 2 == 0 else 15])
        for position in range(64)
    )


@lru_cache(maxsize=None)
def _exogenous(
    update: int, *, mutate_position: int | None = None,
    mutate_observation_position: int | None = None,
):
    rows = []
    for position in range(64):
        roster = 9 if position % 2 == 0 else 15
        marker = position + (1000 if position == mutate_observation_position else 0)
        root = b"U" * 32 if position == mutate_position else b"T" * 32
        tape = generate_episode_tape(
            AddressedRNG(root), seed_block="FRRIE-B01-TEST-ONLY-BLOCK-001",
            purpose="TRAIN", roster=roster, update=update, episode=position // 2,
        )
        roles = np.repeat(np.arange(3, dtype=np.int64), roster // 3)
        masks = np.zeros((12, roster, 6), dtype=np.bool_)
        for entity, role in enumerate(roles):
            masks[:, entity, list(LEGAL_ACTION_INDICES[int(role)])] = True
        rows.append(capture_exogenous_episode(
            update=update, position=position, roster=roster,
            tape=tape,
            observations=np.full((12, roster, 22), marker, dtype=np.float32),
            relations=roles, masks=masks,
            origin_coordinates=((0, 0, 0), (1, 1, roster // 3), (2, 2, 2 * roster // 3)),
        ))
    return tuple(rows)


def _ledger(slots: int = 4_928):
    return BatchWorkLedger(
        _LEDGER_TOKEN, lanes=32, native_reset_calls=64,
        native_observe_calls=512, native_step_calls=1024,
        environment_slots=slots,
    )


def _batch(model, *, update: int, exogenous=None, episodes=None, slots=4_928):
    return B01ArmBatch(
        episodes=_episodes(model) if episodes is None else episodes,
        exogenous_receipts=_exogenous(update) if exogenous is None else exogenous,
        collection_ledgers=(_ledger(slots),),
    )


def _nan_sentinel_episode(torch) -> RSCFEpisode:
    legal = torch.tensor(
        ((1, 1, 0, 0, 0, 1), (1, 1, 0, 0, 0, 1), (0, 0, 1, 1, 1, 1)),
        dtype=torch.bool,
    )
    q_targets = torch.full((3, 6), float("nan"), dtype=torch.float32)
    q_targets[legal] = torch.linspace(0.0, 1.0, int(legal.sum()), dtype=torch.float32)
    return RSCFEpisode(
        roster_size=9,
        selected_probabilities=torch.full((3, 6), 1.0 / 6.0, dtype=torch.float32),
        q_targets=q_targets, legal_masks=legal,
        factual_actions=torch.tensor((0, 1, 2), dtype=torch.int64),
        all_probabilities=torch.full((12, 9, 6), 1.0 / 6.0, dtype=torch.float32),
        critic_values=torch.zeros(12, dtype=torch.float32),
        terminal_return=torch.tensor(0.5, dtype=torch.float32),
    )


def test_paired_q_targets_accept_canonical_illegal_nan_bits_and_reject_drift():
    import torch

    left = _nan_sentinel_episode(torch)
    right = dataclasses.replace(
        left, q_targets=left.q_targets.clone(), legal_masks=left.legal_masks.clone(),
    )
    # Regression: torch.equal(left.q_targets, right.q_targets) is False solely
    # because the authorized illegal-action structural sentinels are NaNs.
    assert not torch.equal(left.q_targets, right.q_targets)
    assert_paired_episode_information((left,), (right,))

    noncanonical_nan = torch.tensor([0x7FC00001], dtype=torch.int32).view(torch.float32)[0]
    drift_left = left.q_targets.clone()
    drift_right = right.q_targets.clone()
    drift_left[0, 2] = noncanonical_nan
    drift_right[0, 2] = noncanonical_nan
    with pytest.raises(B01ContractError, match="different information"):
        assert_paired_episode_information(
            (dataclasses.replace(left, q_targets=drift_left),),
            (dataclasses.replace(right, q_targets=drift_right),),
        )

    legal_drift = right.q_targets.clone()
    legal_drift[0, 0] = torch.nextafter(
        legal_drift[0, 0], torch.tensor(float("inf"), dtype=torch.float32),
    )
    with pytest.raises(B01ContractError, match="different information"):
        assert_paired_episode_information(
            (left,), (dataclasses.replace(right, q_targets=legal_drift),),
        )

    illegal_non_nan = right.q_targets.clone()
    illegal_non_nan[0, 2] = 0.0
    with pytest.raises(B01ContractError, match="different information"):
        assert_paired_episode_information(
            (left,), (dataclasses.replace(right, q_targets=illegal_non_nan),),
        )

    mask_drift = right.legal_masks.clone()
    mask_drift[0, 2] = True
    with pytest.raises(B01ContractError, match="different information"):
        assert_paired_episode_information(
            (left,), (dataclasses.replace(right, legal_masks=mask_drift),),
        )


def test_exact_loss_reduction_provenance_replays_left_fold_and_rejects_tamper():
    import torch

    component_order = ("loss", "score", "entropy", "critic")
    case = None
    for seed in range(64):
        generator = torch.Generator().manual_seed(seed)
        score = torch.randn(64, generator=generator, dtype=torch.float32)
        entropy = 3.0 * torch.rand(64, generator=generator, dtype=torch.float32)
        critic = 4.0 * torch.rand(64, generator=generator, dtype=torch.float32)
        loss = score - 0.01 * entropy + 0.5 * critic
        columns = (loss, score, entropy, critic)
        aggregate = tuple(sum(column) / 64.0 for column in columns)
        separate_recombination = (
            aggregate[1] - 0.01 * aggregate[2] + 0.5 * aggregate[3]
        )
        if int(aggregate[0].view(torch.int32)) != int(
            separate_recombination.view(torch.int32)
        ):
            case = columns, aggregate, separate_recombination
            break
    assert case is not None
    columns, aggregate, separate_recombination = case
    assert int(aggregate[0].view(torch.int32)) != int(
        separate_recombination.view(torch.int32)
    )

    rows = torch.stack(columns, dim=1)
    receipt = {
        "schema": "FRRIE_RSCF_LOSS_REDUCTION_RECEIPT_V1",
        "component_order": list(component_order), "roster_order": list((9, 15) * 32),
        "per_episode_u32_bits": rows.view(torch.int32).to(torch.int64).bitwise_and(
            0xFFFFFFFF
        ).tolist(),
        "reduction_law": "PYTHON_SUM_INT0_LEFT_FOLD_THEN_DIVIDE_FLOAT64_LITERAL_64",
        "divisor": 64, "dtype": "CPU_FP32",
        "aggregate_u32_bits": [
            int(value.view(torch.int32)) & 0xFFFFFFFF for value in aggregate
        ],
    }
    scalars = {name: float(value) for name, value in zip(component_order, aggregate)}
    assert validate_loss_reduction_receipt(
        receipt, aggregate_scalars=scalars,
    )["exact_replay_validated"] is True

    episode_tamper = json.loads(json.dumps(receipt))
    episode_tamper["per_episode_u32_bits"][0][1] ^= 1
    with pytest.raises(ContractError, match="episode composite"):
        validate_loss_reduction_receipt(episode_tamper, aggregate_scalars=scalars)

    order_tamper = json.loads(json.dumps(receipt))
    order_tamper["roster_order"][0:2] = [15, 9]
    with pytest.raises(ContractError, match="identity/order"):
        validate_loss_reduction_receipt(order_tamper, aggregate_scalars=scalars)

    divisor_tamper = {**receipt, "divisor": 63}
    with pytest.raises(ContractError, match="identity/order"):
        validate_loss_reduction_receipt(divisor_tamper, aggregate_scalars=scalars)

    aggregate_tamper = json.loads(json.dumps(receipt))
    aggregate_tamper["aggregate_u32_bits"][0] ^= 1
    with pytest.raises(ContractError, match="aggregate bits"):
        validate_loss_reduction_receipt(aggregate_tamper, aggregate_scalars=scalars)

    for invalid_bits in (False, -1, 0x1_0000_0000):
        invalid_receipt = json.loads(json.dumps(receipt))
        invalid_receipt["aggregate_u32_bits"][2] = invalid_bits
        with pytest.raises(ContractError, match="identity/order"):
            validate_loss_reduction_receipt(invalid_receipt, aggregate_scalars=scalars)

    for invalid_scalar in (False, float("nan"), float("inf"), float("-inf")):
        invalid_scalars = {**scalars, "entropy": invalid_scalar}
        with pytest.raises(ContractError, match="identity/order"):
            validate_loss_reduction_receipt(receipt, aggregate_scalars=invalid_scalars)


def _receipt(arm: str, update: int, indices=()):
    return ArmUpdateReceipt(
        arm=arm, update=update, loss=0.0, score=0.0, entropy=0.0, critic=0.0,
        loss_reduction_receipt=LossReductionReceipt(
            schema="FRRIE_RSCF_LOSS_REDUCTION_RECEIPT_V1",
            component_order=("loss", "score", "entropy", "critic"),
            roster_order=(9, 15) * 32,
            per_episode_u32_bits=((0, 0, 0, 0),) * 64,
            reduction_law="PYTHON_SUM_INT0_LEFT_FOLD_THEN_DIVIDE_FLOAT64_LITERAL_64",
            divisor=64, dtype="CPU_FP32", aggregate_u32_bits=(0, 0, 0, 0),
        ),
        preclip_global_norm=0.5, backward_calls=1, adam_steps=1,
        projection_changed_indices=tuple(indices), box_contact=bool(indices),
        maximum_box_overshoot=0.1 if indices else 0.0,
        projection_displacement=0.2 if indices else 0.0,
        preprojection_beta=tuple([0.2] * 18), postprojection_beta=tuple([0.15] * 18),
        optimizer_moments_unchanged_by_projection=True,
        model_pre_bytes=b"model-pre", optimizer_pre_bytes=b"optimizer-pre",
        model_post_adam_bytes=b"model-post-adam",
        optimizer_post_adam_bytes=b"optimizer-post-adam",
        model_post_projection_bytes=b"model-post-projection",
        optimizer_post_projection_bytes=b"optimizer-post-projection",
    )


def test_direct_envelope_rejects_different_tape_or_observation_and_actual_ledger_short_one(tmp_path):
    _admit(tmp_path)
    models, _ = _models()
    left = _batch(models["PHY_TRUST"], update=1)
    right = _batch(models["PHY_TRUST"], update=1, exogenous=_exogenous(1, mutate_position=7))
    with pytest.raises(B01ContractError, match="exogenous"):
        assert_common_exogenous_and_work(left, right)
    observations_differ = _batch(
        models["PHY_TRUST"], update=1,
        exogenous=_exogenous(1, mutate_observation_position=7),
    )
    # Observation values are not common exogenous data post-contact.
    assert_common_exogenous_and_work(left, observations_differ)
    with pytest.raises(B01ContractError, match="pre-contact actual observation"):
        assert_precontact_observation_equality(left, observations_differ)
    with pytest.raises(B01ContractError, match="4928"):
        _batch(models["PHY_TRUST"], update=1, slots=4_927).validate(update=1)

    tape = generate_episode_tape(
        AddressedRNG(b"T" * 32), seed_block="FRRIE-B01-TEST-ONLY-BLOCK-001",
        purpose="TRAIN", roster=9, update=1, episode=0,
    )
    roles = np.repeat(np.arange(3, dtype=np.int64), 3)
    masks = np.zeros((12, 9, 6), dtype=np.bool_)
    for entity, role in enumerate(roles):
        masks[:, entity, list(LEGAL_ACTION_INDICES[int(role)])] = True
    common = dict(
        update=1, position=0, roster=9, tape=tape, relations=roles, masks=masks,
        origin_coordinates=((0, 0, 0), (1, 1, 3), (2, 2, 6)),
    )
    with pytest.raises(B01ContractError, match="FP32"):
        capture_exogenous_episode(
            **common, observations=np.zeros((12, 9, 22), dtype=np.int32),
        )
    bad_masks = np.ones((12, 9, 6), dtype=np.bool_)
    with pytest.raises(B01ContractError, match="exact per-role"):
        capture_exogenous_episode(
            **dict(common, masks=bad_masks),
            observations=np.zeros((12, 9, 22), dtype=np.float32),
        )


def test_projection_receipt_contains_loss_parts_beta_values_and_real_indices(tmp_path):
    _admit(tmp_path)
    models, optimizers = _models()
    import torch
    with torch.no_grad():
        models["PHY_TRUST"].beta.fill_(2.0)
    receipt = ProjectionObservedTrainer(
        models["PHY_TRUST"], optimizers["PHY_TRUST"],
    ).update(_episodes(models["PHY_TRUST"]), update=1)
    assert receipt.box_contact is True
    assert receipt.projection_changed_indices == tuple(range(18))
    assert len(receipt.preprojection_beta) == len(receipt.postprojection_beta) == 18
    assert all(np.isfinite(value) for value in (
        receipt.loss, receipt.score, receipt.entropy, receipt.critic,
        receipt.preclip_global_norm,
    ))
    assert receipt.optimizer_moments_unchanged_by_projection is True
    assert receipt.model_pre_bytes
    assert receipt.optimizer_pre_bytes
    assert receipt.model_post_adam_bytes != receipt.model_post_projection_bytes
    assert receipt.optimizer_post_adam_bytes == receipt.optimizer_post_projection_bytes
    assert decode_optimizer_state(receipt.optimizer_pre_bytes).step == 0
    assert decode_optimizer_state(receipt.optimizer_post_adam_bytes).step == 1
    assert models["PHY_TRUST"].parameter_bytes() == receipt.model_post_projection_bytes
    assert encode_optimizer_state(
        models["PHY_TRUST"], optimizers["PHY_TRUST"],
    ) == receipt.optimizer_post_projection_bytes


def test_postcontact_different_derived_batches_are_allowed_with_same_direct_envelope(tmp_path):
    _admit(tmp_path)
    models, optimizers = _models()
    import torch
    with torch.no_grad():
        models["EDGE_FLEX"].beta.add_(0.2)
    paired = PairedB01Trainer(models, optimizers)
    paired.first_tight_contact_update = 1
    left_common = _exogenous(2)
    right_common = _exogenous(2, mutate_observation_position=7)
    batches = {
        "PHY_TRUST": _batch(models["PHY_TRUST"], update=2, exogenous=left_common),
        "EDGE_FLEX": _batch(models["EDGE_FLEX"], update=2, exogenous=right_common),
    }
    assert not torch.equal(
        batches["PHY_TRUST"].episodes[0].selected_probabilities,
        batches["EDGE_FLEX"].episodes[0].selected_probabilities,
    )
    receipts = paired.update(batches, update=2)
    assert set(receipts) == {"PHY_TRUST", "EDGE_FLEX"}


def test_edge_failure_rolls_back_both_arms_and_audit(tmp_path):
    _admit(tmp_path)
    models, optimizers = _models()
    paired = PairedB01Trainer(models, optimizers)
    paired.first_tight_contact_update = 1
    common = _exogenous(2)
    edge_episodes = list(_episodes(models["EDGE_FLEX"]))
    edge_episodes[0] = dataclasses.replace(
        edge_episodes[0], q_targets=edge_episodes[0].q_targets.clone().fill_(float("nan")),
    )
    batches = {
        "PHY_TRUST": _batch(models["PHY_TRUST"], update=2, exogenous=common),
        "EDGE_FLEX": _batch(models["EDGE_FLEX"], update=2, exogenous=common, episodes=tuple(edge_episodes)),
    }
    before = {
        arm: (models[arm].parameter_bytes(), encode_optimizer_state(models[arm], optimizers[arm]))
        for arm in models
    }
    audit = paired.projection_audit()
    with pytest.raises(B01ContractError, match="rolled back"):
        paired.update(batches, update=2)
    assert paired.projection_audit() == audit
    assert all(
        models[arm].parameter_bytes() == before[arm][0]
        and encode_optimizer_state(models[arm], optimizers[arm]) == before[arm][1]
        for arm in models
    )


def test_no_contact_postcondition_divergence_rolls_back_and_coordinate_union_is_real(tmp_path):
    _admit(tmp_path)
    models, optimizers = _models()
    paired = PairedB01Trainer(models, optimizers)
    batches = {arm: _batch(models[arm], update=1) for arm in models}
    paired.trainers["PHY_TRUST"].update = lambda episodes, update: _receipt("PHY_TRUST", update)

    def diverge(episodes, update):
        import torch
        with torch.no_grad():
            models["EDGE_FLEX"].action_head.bias[0].add_(1.0)
        return _receipt("EDGE_FLEX", update)

    paired.trainers["EDGE_FLEX"].update = diverge
    before = {arm: models[arm].parameter_bytes() for arm in models}
    audit = paired.projection_audit()
    with pytest.raises(B01ContractError, match="rolled back"):
        paired.update(batches, update=1)
    assert paired.projection_audit() == audit
    assert all(models[arm].parameter_bytes() == before[arm] for arm in models)

    # Direct receipt indices, not range(count), form the cross-update union.
    paired.trainers["PHY_TRUST"].update = lambda episodes, update: _receipt(
        "PHY_TRUST", update, (1, 3) if update == 1 else (3, 5),
    )
    paired.trainers["EDGE_FLEX"].update = lambda episodes, update: _receipt("EDGE_FLEX", update)
    paired.update(batches, update=1)
    batches2 = {arm: dataclasses.replace(batches[arm], exogenous_receipts=_exogenous(2)) for arm in models}
    paired.update(batches2, update=2)
    assert paired.changed_coordinates == {1, 3, 5}
    assert paired.projection_audit()["tight_projection_changed_coordinates"] == 3
