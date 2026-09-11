from __future__ import annotations

import struct

import numpy as np
import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.b01 import (
    training_shards as training_shards_module,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.arms import (
    PARAMETER_BYTE_COUNT,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.contract import (
    B01ContractError, canonical_json_bytes,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.training_shards import (
    ActualDirectTrainingRow,
    SyntheticPairedResumeRow,
    SyntheticSparseTrainingRow,
    SyntheticTrainingRow,
    direct_training_row_contract,
    validate_synthetic_resume_suffix_fixture,
    validate_actual_paired_direct_rows,
    validate_synthetic_training_row,
    write_synthetic_training_fixture,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01.trainer import (
    validate_direct_training_shard,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.state_codec import (
    OPTIMIZER_PAYLOAD_BYTE_COUNT,
    OPTIMIZER_STATE_BYTE_COUNT,
    OPTIMIZER_STATE_MAGIC,
    OPTIMIZER_STATE_VERSION,
)


def _optimizer(step: int) -> bytes:
    header = struct.pack(
        "<8sII", OPTIMIZER_STATE_MAGIC, OPTIMIZER_STATE_VERSION,
        OPTIMIZER_PAYLOAD_BYTE_COUNT,
    )
    return header + bytes(OPTIMIZER_PAYLOAD_BYTE_COUNT - 8) + struct.pack("<Q", step)


def _valid_row(update: int = 1) -> SyntheticTrainingRow:
    model = bytes(PARAMETER_BYTE_COUNT)
    optimizer_pre = _optimizer(update - 1)
    optimizer_post = _optimizer(update)
    arrays = {
        "beta_pre_bits": bytes(18 * 4),
        "beta_post_adam_bits": bytes(18 * 4),
        "beta_post_projection_bits": bytes(18 * 4),
        "loss_terms": bytes(5 * 4),
        "loss_episode_component_bits": bytes(64 * 4 * 4),
        "loss_aggregate_bits": bytes(4 * 4),
        "changed_mask": bytes(18),
        "box_contact": bytes(1),
        "maximum_box_overshoot": bytes(8),
        "projection_l1_displacement": bytes(8),
        "optimizer_moments_unchanged": bytes([1]),
        "work": np.asarray([768, 2912, 1248, 4928], dtype="<u4").tobytes(),
        "raw_native_calls": bytes(3 * 4),
    }
    blobs = {
        "model_pre": model,
        "model_post_adam": model,
        "model_post_projection": model,
        "optimizer_pre": optimizer_pre,
        "optimizer_post_adam": optimizer_post,
        "optimizer_post_projection": optimizer_post,
    }
    return SyntheticTrainingRow(update=update, array_shards=arrays, state_blobs=blobs)


class _SinglePassRows:
    def __init__(self, updates):
        self._updates = updates
        self.iterations = 0

    def __iter__(self):
        self.iterations += 1
        if self.iterations != 1:
            raise AssertionError("row source was traversed more than once")
        for update in self._updates:
            yield SyntheticSparseTrainingRow(update)


def test_sparse_fixture_is_exact_size_descriptor_only_and_single_pass(tmp_path):
    rows = _SinglePassRows(range(1, 513))
    receipt = write_synthetic_training_fixture(
        rows, directory=tmp_path, seed_label="TEST-S001", arm="PHY_TRUST",
        sparse=True,
    )
    assert rows.iterations == 1
    assert receipt["schema"] == "FRRIE_B01_SYNTHETIC_SPARSE_DESCRIPTOR_FIXTURE_V1"
    assert receipt["role"] == "SYNTHETIC_COMPONENT_ONLY"
    assert receipt["max_buffered_rows"] == 1
    assert receipt["production_token"] is False
    assert receipt["training_validation_replay_complete"] is False
    assert receipt["payload_validated"] is False
    assert receipt["row_payloads_validated"] is False
    assert receipt["canonical_full512_validation_complete"] is False
    assert receipt["canonical_training_shard"] is None
    assert "complete" not in receipt
    shards = receipt["descriptor_shards"]
    contract = direct_training_row_contract()
    for group in ("array_shards", "state_blobs"):
        assert set(shards[group]) == set(contract[group])
        for name, descriptor in shards[group].items():
            dtype, row_shape = contract[group][name]
            expected_shape = [512, *row_shape]
            assert descriptor == {
                "path": str(tmp_path.joinpath(f"{group}__{name}.raw").resolve()),
                "dtype": dtype,
                "shape": expected_shape,
                "order": "C",
                "byte_count": 512 * int(np.prod(row_shape, dtype=np.int64))
                * np.dtype(dtype).itemsize,
            }
            assert tmp_path.joinpath(f"{group}__{name}.raw").stat().st_size == descriptor["byte_count"]
    with pytest.raises(B01ContractError, match="fields differ"):
        validate_direct_training_shard(receipt["canonical_training_shard"])


@pytest.mark.parametrize(
    ("updates", "match"),
    [
        (range(1, 512), "exactly 512"),
        (range(1, 514), "exactly 512"),
        ([1, 2, 2], "strict update order"),
        ([1, 3], "strict update order"),
    ],
)
def test_sparse_writer_rejects_511_513_duplicate_and_order(tmp_path, updates, match):
    with pytest.raises(B01ContractError, match=match):
        write_synthetic_training_fixture(
            (SyntheticSparseTrainingRow(i) for i in updates),
            directory=tmp_path, seed_label="TEST-S001", arm="EDGE_FLEX", sparse=True,
        )


def test_writer_rejects_non_test_identity_and_launch_or_production_flags(tmp_path):
    rows = (SyntheticSparseTrainingRow(i) for i in range(1, 513))
    with pytest.raises(B01ContractError, match="TEST seed"):
        write_synthetic_training_fixture(
            rows, directory=tmp_path, seed_label="S001", arm="PHY_TRUST", sparse=True,
        )
    for flag in ("production", "launch"):
        kwargs = {flag: True}
        with pytest.raises(B01ContractError, match="never production or launch"):
            write_synthetic_training_fixture(
                (SyntheticSparseTrainingRow(i) for i in range(1, 513)),
                directory=tmp_path, seed_label="TEST-S001", arm="PHY_TRUST",
                sparse=True, **kwargs,
            )


def test_small_core_row_law_and_tamper_rejection():
    row = _valid_row()
    validated = validate_synthetic_training_row(row, arm="PHY_TRUST")
    assert validated["schema"] == "FRRIE_B01_SYNTHETIC_TRAINING_ROW_VALIDATED_V1"
    assert validated["training_validation_replay_complete"] is False
    assert validated["update"] == 1
    assert validated["next_model_bytes"] == row.state_blobs["model_post_projection"]
    assert validated["next_optimizer_bytes"] == row.state_blobs["optimizer_post_projection"]

    bad_work = dict(row.array_shards)
    bad_work["work"] = np.asarray([768, 2911, 1248, 4927], dtype="<u4").tobytes()
    with pytest.raises(B01ContractError, match="work partition"):
        validate_synthetic_training_row(
            SyntheticTrainingRow(row.update, bad_work, row.state_blobs), arm="PHY_TRUST",
        )

    bad_step = dict(row.state_blobs)
    bad_step["optimizer_post_projection"] = _optimizer(2)
    with pytest.raises(B01ContractError, match="Adam step frontier"):
        validate_synthetic_training_row(
            SyntheticTrainingRow(row.update, row.array_shards, bad_step), arm="PHY_TRUST",
        )

    bad_loss = dict(row.array_shards)
    bad_loss["loss_aggregate_bits"] = struct.pack("<IIII", 1, 0, 0, 0)
    with pytest.raises(B01ContractError, match="loss reduction"):
        validate_synthetic_training_row(
            SyntheticTrainingRow(row.update, bad_loss, row.state_blobs), arm="PHY_TRUST",
        )


def test_row_chain_is_direct():
    row = _valid_row(2)
    with pytest.raises(B01ContractError, match="consecutive state chain"):
        validate_synthetic_training_row(
            row, arm="PHY_TRUST",
            previous_model_post_projection=b"x" * PARAMETER_BYTE_COUNT,
            previous_optimizer_post_projection=_optimizer(1),
        )
    with pytest.raises(B01ContractError, match="both absent or both present"):
        validate_synthetic_training_row(
            row, arm="PHY_TRUST",
            previous_model_post_projection=row.state_blobs["model_pre"],
        )


def test_typed_row_rejects_inventory_and_exact_byte_tamper():
    row = _valid_row()
    missing = dict(row.array_shards)
    missing.pop("loss_terms")
    with pytest.raises(B01ContractError, match="inventory"):
        validate_synthetic_training_row(
            SyntheticTrainingRow(row.update, missing, row.state_blobs), arm="PHY_TRUST",
        )
    truncated = dict(row.state_blobs)
    truncated["model_pre"] = truncated["model_pre"][:-1]
    with pytest.raises(B01ContractError, match="byte length"):
        validate_synthetic_training_row(
            SyntheticTrainingRow(row.update, row.array_shards, truncated), arm="PHY_TRUST",
        )


def test_dense_writer_rejects_sparse_rows_without_allocating_full_fixture(tmp_path):
    with pytest.raises(B01ContractError, match="typed dense row"):
        write_synthetic_training_fixture(
            (SyntheticSparseTrainingRow(1),), directory=tmp_path,
            seed_label="TEST-S001", arm="PHY_TRUST", sparse=False,
        )


def test_dense_finalize_is_synthetic_descriptor_not_canonical_certification(
    tmp_path, monkeypatch,
):
    tiny_contract = {
        "array_shards": {"tiny": ("|u1", ())},
        "state_blobs": {},
    }
    monkeypatch.setattr(
        training_shards_module, "direct_training_row_contract", lambda: tiny_contract,
    )
    monkeypatch.setattr(
        training_shards_module,
        "validate_synthetic_training_row",
        lambda *args, **kwargs: {
            "next_model_bytes": b"", "next_optimizer_bytes": b"",
        },
    )
    receipt = write_synthetic_training_fixture(
        (SyntheticTrainingRow(i, {"tiny": b"x"}, {}) for i in range(1, 513)),
        directory=tmp_path, seed_label="TEST-S001", arm="PHY_TRUST", sparse=False,
    )
    assert receipt["schema"] == "FRRIE_B01_SYNTHETIC_DENSE_DESCRIPTOR_FIXTURE_V1"
    assert receipt["canonical_training_shard"] is None
    assert receipt["canonical_full512_validation_complete"] is False
    assert receipt["training_validation_replay_complete"] is False
    assert receipt["row_payloads_validated"] is True
    assert "complete" not in receipt
    assert receipt["descriptor_shards"]["array_shards"]["tiny"]["shape"] == [512]
    with pytest.raises(B01ContractError, match="fields differ"):
        validate_direct_training_shard(receipt["canonical_training_shard"])


class _SinglePassResumeRows:
    def __init__(self, rows):
        self._rows = rows
        self.iterations = 0

    def __iter__(self):
        self.iterations += 1
        if self.iterations != 1:
            raise AssertionError("resume row source was traversed more than once")
        yield from self._rows


def _resume_row(update: int, *, tape: bytes | None = None, edge_tag: bytes = b""):
    return SyntheticPairedResumeRow(
        update=update,
        address_tape_receipt_bytes=tape or f"tape-{update}".encode("ascii"),
        arm_rows={
            "PHY_TRUST": SyntheticTrainingRow(update, {"tag": b"phy"}, {}),
            "EDGE_FLEX": SyntheticTrainingRow(update, {"tag": b"edge" + edge_tag}, {}),
        },
    )


def test_resume_suffix_fixture_covers_every_update_after_checkpoint_once(monkeypatch):
    calls = []

    def validate(row, *, arm, previous_model_post_projection,
                 previous_optimizer_post_projection):
        calls.append((row.update, arm, previous_model_post_projection,
                      previous_optimizer_post_projection))
        return {
            "next_model_bytes": f"model-{arm}-{row.update}".encode("ascii"),
            "next_optimizer_bytes": f"optimizer-{arm}-{row.update}".encode("ascii"),
        }

    monkeypatch.setattr(
        training_shards_module, "validate_synthetic_training_row", validate,
    )
    states = {
        arm: {"model_state_bytes": f"model-{arm}-256".encode("ascii"),
              "optimizer_state_bytes": f"optimizer-{arm}-256".encode("ascii")}
        for arm in ("PHY_TRUST", "EDGE_FLEX")
    }
    left = _SinglePassResumeRows([_resume_row(i) for i in range(257, 513)])
    right = _SinglePassResumeRows([_resume_row(i) for i in range(257, 513)])
    receipt = validate_synthetic_resume_suffix_fixture(
        checkpoint=256, checkpoint_states=states,
        uninterrupted_rows=left, resumed_rows=right,
    )
    assert left.iterations == right.iterations == 1
    assert receipt == {
        "schema": "FRRIE_B01_SYNTHETIC_RESUME_SUFFIX_COMPONENT_V1",
        "role": "SYNTHETIC_COMPONENT_ONLY",
        "checkpoint": 256, "first_update": 257, "last_update": 512,
        "update_count": 256,
        "direct_state_work_loss_bytes_equal": True,
        "common_address_tape_bytes_equal": True,
        "checkpoint_state_direct_bytes_supplied": True,
        "checkpoint_codec_or_restore_validated": False,
        "state_chain_from_checkpoint_validated": True,
        "terminal_empty_suffix_only": False,
        "authoritative_full512_validation_complete": False,
        "training_validation_replay_complete": False,
        "production_token": False,
    }
    assert len(calls) == 256 * 2 * 2
    assert calls[0][2:] == (
        b"model-PHY_TRUST-256", b"optimizer-PHY_TRUST-256",
    )


def test_resume_suffix_fixture_terminal_and_direct_tamper_fail_closed(monkeypatch):
    monkeypatch.setattr(
        training_shards_module, "validate_synthetic_training_row",
        lambda row, **kwargs: {
            "next_model_bytes": b"model", "next_optimizer_bytes": b"optimizer",
        },
    )
    states = {
        arm: {"model_state_bytes": b"model", "optimizer_state_bytes": b"optimizer"}
        for arm in ("PHY_TRUST", "EDGE_FLEX")
    }
    terminal = validate_synthetic_resume_suffix_fixture(
        checkpoint=512, checkpoint_states=states,
        uninterrupted_rows=(), resumed_rows=(),
    )
    assert terminal["update_count"] == 0
    assert terminal["first_update"] is terminal["last_update"] is None
    assert terminal["checkpoint_codec_or_restore_validated"] is False
    assert terminal["state_chain_from_checkpoint_validated"] is False
    assert terminal["terminal_empty_suffix_only"] is True

    left = [_resume_row(i) for i in range(257, 513)]
    right = list(left)
    right[10] = _resume_row(267, tape=b"different-tape")
    with pytest.raises(B01ContractError, match="address/tape bytes differ"):
        validate_synthetic_resume_suffix_fixture(
            checkpoint=256, checkpoint_states=states,
            uninterrupted_rows=left, resumed_rows=right,
        )
    right = list(left)
    right[10] = _resume_row(267, edge_tag=b"-tampered")
    with pytest.raises(B01ContractError, match="direct arm row bytes differ"):
        validate_synthetic_resume_suffix_fixture(
            checkpoint=256, checkpoint_states=states,
            uninterrupted_rows=left, resumed_rows=right,
        )
    with pytest.raises(B01ContractError, match="exact update range"):
        validate_synthetic_resume_suffix_fixture(
            checkpoint=256, checkpoint_states=states,
            uninterrupted_rows=left[:-1], resumed_rows=left[:-1],
        )


def _pure_expected_receipts(update=1, seed="FRRIE-B01-TEST-ONLY-BLOCK-001"):
    from experiments.candidates.finite_resource_relational_inductive_efficiency.policy import (
        LEGAL_ACTION_INDICES,
    )

    result = []
    for position in range(64):
        roster = 9 if position % 2 == 0 else 15
        roles = np.repeat(np.arange(3, dtype=np.int64), roster // 3)
        masks = np.zeros((12, roster, 6), dtype=np.bool_)
        for entity, role in enumerate(roles):
            masks[:, entity, list(LEGAL_ACTION_INDICES[int(role)])] = True
        origins = tuple((role, role, role * (roster // 3)) for role in range(3))
        addresses = tuple(canonical_json_bytes({
            "schema": "FRRIE_B01_ORIGIN_ADDRESS_V1", "seed_block": seed,
            "update": update, "batch_position": position, "roster": roster,
            "role": role, "slot": slot, "entity": entity,
        }) for role, slot, entity in origins)
        tape_size = (
            2 * 3 * 8 + 12 * 2 * (roster // 3) * 4
            + 12 * roster * roster * 4 + 12 * roster * 4 + 12 * roster * 4
        )
        result.append({
            "update": update, "position": position, "roster": roster,
            "tape_bytes": bytes([position]) * tape_size,
            "tape_coordinate": (seed, "TRAIN", roster, update, position // 2),
            "law_revisions": (
                "RIDGEGATE_2Z_NATIVE_STEP_ABI_V2", "OBSERVATION_22_V1",
                "K0_RELATION_FUNCTION_V1", "ROLE_LEGAL_MASK_FUNCTION_V1",
            ),
            "relations_bytes": roles.tobytes(), "relations_shape": (roster,),
            "relations_dtype": "int64", "masks_bytes": masks.tobytes(),
            "masks_shape": (12, roster, 6), "masks_dtype": "bool",
            "origin_coordinates": origins, "origin_addresses": addresses,
        })
    return tuple(result)


def test_actual_paired_receipts_reject_identical_common_mode_corruption(monkeypatch):
    from types import SimpleNamespace
    from experiments.candidates.finite_resource_relational_inductive_efficiency.b01 import (
        batch_collector as collector_module,
    )

    expected = _pure_expected_receipts()
    class Raw:
        def __init__(self, value):
            self.value = value

        def tobytes(self, order="C"):
            assert order == "C"
            return self.value

    tapes = []
    origins = []
    for row in expected:
        tapes.append(SimpleNamespace(
            event_times=Raw(row["tape_bytes"]), detection_uniform=Raw(b""),
            uplink_uniform=Raw(b""), base_uniform=Raw(b""), action_uniform=Raw(b""),
        ))
        origins.append(tuple(
            SimpleNamespace(role=role, slot=slot, entity=entity)
            for role, slot, entity in row["origin_coordinates"]
        ))
    monkeypatch.setattr(
        collector_module, "make_test_update_inputs",
        lambda *args, **kwargs: (tuple(tapes), tuple(origins)),
    )
    rows = {
        arm: ActualDirectTrainingRow(
            update=1, arm=arm,
            array_shards={"work": b"work", "raw_native_calls": b"native"},
            state_blobs={}, typed_exogenous_receipts=expected,
        )
        for arm in ("PHY_TRUST", "EDGE_FLEX")
    }
    receipt = validate_actual_paired_direct_rows(
        rows, expected_update=1,
        expected_seed_label="FRRIE-B01-TEST-ONLY-BLOCK-001",
        expected_root=b"R" * 32,
    )
    assert receipt["typed_tape_address_equal"] is True
    tampered = list(expected)
    tampered[0] = dict(tampered[0])
    tampered[0]["tape_bytes"] = b"x" + tampered[0]["tape_bytes"][1:]
    common_wrong = {
        arm: ActualDirectTrainingRow(
            update=1, arm=arm, array_shards=rows[arm].array_shards,
            state_blobs={}, typed_exogenous_receipts=tuple(tampered),
        )
        for arm in rows
    }
    with pytest.raises(B01ContractError, match="root-regenerated canonical input"):
        validate_actual_paired_direct_rows(
            common_wrong, expected_update=1,
            expected_seed_label="FRRIE-B01-TEST-ONLY-BLOCK-001",
            expected_root=b"R" * 32,
        )
