from __future__ import annotations

import torch

from experiments.candidates.dual_epoch_receipt_survival.domain import (
    GRU_DUAL, GRU_ORACLE, GRU_RAW, GRU_SNAPSHOT, GRU_UNBOUND,
    GRU_VALIDITY, LEARNED_ARMS,
)
from experiments.candidates.dual_epoch_receipt_survival.generator import generate_examples
from experiments.candidates.dual_epoch_receipt_survival.learner import (
    BATCH_SIZE, EPOCHS, GRAD_CLIP, OPTIMIZER, MatchedGRU, new_model,
    parameter_count, train_arm,
)
from experiments.candidates.dual_epoch_receipt_survival.schema import (
    FLAG_INDICES, KINDS, MASK_CONTRACT, PADDING_INDEX, TOKEN_SCHEMA,
    encode_example,
)


def test_schema_is_exact_binary_6_by_192_with_zero_padding_and_raw_has_no_composites():
    row = generate_examples(13, "test")[0]
    for arm in LEARNED_ARMS:
        encoded = encode_example(row, arm)
        assert encoded.shape == (6, 192)
        assert encoded.dtype == torch.float32
        assert set(encoded.unique().tolist()) <= {0.0, 1.0}
        assert not encoded[:, PADDING_INDEX].any()
    raw = encode_example(row, GRU_RAW)
    assert not raw[:, FLAG_INDICES["live"]].any()
    assert not raw[:, FLAG_INDICES["bottom"]].any()
    assert TOKEN_SCHEMA["width"] == 192
    assert TOKEN_SCHEMA["sequence_length"] == 6
    assert set(MASK_CONTRACT) >= set(LEARNED_ARMS)


def test_summary_histories_are_masks_and_information_partitions_are_exact_within_superblock():
    block = generate_examples(13, "test")[:16]
    for arm in (GRU_DUAL, GRU_SNAPSHOT, GRU_UNBOUND, GRU_VALIDITY, GRU_ORACLE):
        tensors = [encode_example(row, arm) for row in block]
        assert all(torch.all(token[:5, KINDS["MASK"]] == 1) for token in tensors)
        assert all(torch.count_nonzero(token[:5]) == 5 for token in tensors)

    def same_when(arm, key):
        groups = {}
        for row in block:
            tensor = encode_example(row, arm)
            prior = groups.setdefault(key(row), tensor)
            assert torch.equal(prior, tensor)

    same_when(GRU_SNAPSHOT, lambda _row: ())
    same_when(GRU_UNBOUND, lambda row: (row.authentication, row.displayed_bit))
    same_when(GRU_VALIDITY, lambda row: row.live)
    same_when(GRU_DUAL, lambda row: (row.live, row.displayed_bit if row.live else None))
    same_when(GRU_ORACLE, lambda row: (
        row.authentication, row.owner_survives, row.lease_survives, row.displayed_bit
    ))
    snapshot_labels = {int(row.correct_action) for row in block}
    assert snapshot_labels == {0, 1, 2}


def test_raw_chronology_and_kind_are_sufficient_edge_locators_without_edge_metadata():
    row = generate_examples(13, "test")[0]
    raw = encode_example(row, GRU_RAW)
    owner_positions = [index for index, event in enumerate(row.events)
                       if event.__class__.__name__ == "OwnerUpdate"]
    lease_positions = [index for index, event in enumerate(row.events)
                       if event.__class__.__name__ == "LeaseUpdate"]
    assert [row.events[index].edge for index in owner_positions] == [1, 2]
    assert [row.events[index].edge for index in lease_positions] == [1, 2]
    assert all(raw[index, KINDS["OWNER_UPDATE"]] == 1 for index in owner_positions)
    assert all(raw[index, KINDS["LEASE_UPDATE"]] == 1 for index in lease_positions)


def test_exact_capacity_optimizer_and_registered_training_envelope():
    model = MatchedGRU()
    assert model.gru.input_size == 192
    assert model.gru.hidden_size == 48
    assert model.gru.num_layers == 1
    assert model.gru.dropout == 0
    assert model.head.in_features == 48 and model.head.out_features == 3
    assert parameter_count(model) == 34_995
    assert not any("embedding" in name for name, _ in model.named_parameters())
    assert EPOCHS == 20 and BATCH_SIZE == 256 and GRAD_CLIP == 1.0
    assert OPTIMIZER == {
        "name": "AdamW", "lr": 0.001, "betas": (0.9, 0.999),
        "eps": 1e-8, "weight_decay": 1e-4,
    }


def test_paired_initial_values_are_equal_but_parameter_storage_is_independent():
    left = new_model(59)
    right = new_model(59)
    for a, b in zip(left.parameters(), right.parameters(), strict=True):
        assert torch.equal(a, b)
        assert a.data_ptr() != b.data_ptr()


def test_tiny_engineering_only_training_path_updates_one_independent_model():
    examples = generate_examples(13, "test")[:32]
    model = new_model(13)
    before = [parameter.detach().clone() for parameter in model.parameters()]
    report = train_arm(model, examples, GRU_DUAL, 13, epochs=1, batch_size=16)
    assert report.epochs == 1 and report.batches == 2 and report.example_passes == 32
    assert any(not torch.equal(old, new) for old, new in zip(before, model.parameters(), strict=True))
