from __future__ import annotations

from dataclasses import replace
import inspect

import pytest
import torch

from experiments.candidates.ucope.conditioning_discriminator_r01.conditioning import (
    ConditioningTransformError,
    TransformRecord,
    build_transform,
    pair_initial_coefficients,
    transform_features,
)
from experiments.candidates.ucope.conditioning_discriminator_r01.contract import (
    ARM_IDS,
    CHECKPOINT_ROOT_UPDATES,
    CONTEXTS,
    K_EVAL,
    K_TRAIN,
    SEED_IDS,
    TEN_STRATA,
    ConditioningConfig,
    ContractError,
)


def _full_rank(rows: int, columns: int) -> torch.Tensor:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(1731 + columns)
    random = torch.randn((rows, columns), generator=generator, dtype=torch.float32)
    scales = torch.linspace(0.75, 2.25, columns, dtype=torch.float32)
    return random * scales + torch.eye(rows, columns, dtype=torch.float32)


def test_exact_pro_literals_and_immutable_configuration():
    config = ConditioningConfig.r01()
    assert config.object_id == "UCOPE-B-EXPLORE-FT-XF-BC-INVERTIBLE-CONDITIONING-DISCRIMINATOR-R01"
    assert ARM_IDS == ("FT-XF-BC-RAW", "FT-XF-BC-WHITENED")
    assert SEED_IDS == (
        "ucope-bc-conditioning-r01-fresh-00",
        "ucope-bc-conditioning-r01-fresh-01",
        "ucope-bc-conditioning-r01-fresh-02",
    )
    assert (len(CONTEXTS), K_TRAIN, K_EVAL) == (8, (1, 3, 5, 7, 9), (2, 4, 6, 8))
    assert TEN_STRATA == tuple((action, k) for action in ("PROBE", "IMMEDIATE") for k in K_TRAIN)
    assert (config.episodes_per_context, config.fold_ids) == (5120, (0, 1))
    assert (config.tail_basis_dim, config.root_basis_dim, config.trainable_coefficients) == (5, 7, 12)
    assert (config.tail_updates, config.root_updates, config.checkpoint_root_updates) == (160, 320, CHECKPOINT_ROOT_UPDATES)
    assert (config.dtype, config.loss, config.batch_size) == ("float32", "squared_regression", 256)
    assert config.optimizer.name == "AdamW"
    assert (config.optimizer.learning_rate, config.optimizer.betas, config.optimizer.epsilon) == (3e-4, (0.9, 0.999), 1e-8)
    assert (config.optimizer.weight_decay, config.optimizer.gradient_norm_clip) == (0.0, 1.0)
    with pytest.raises(ContractError, match="configuration drift"):
        replace(config, root_updates=321).validate()


@pytest.mark.parametrize(("stage", "dimension"), (("tail", 5), ("root", 7)))
def test_feature_only_transform_is_direct_fp32_gram_cholesky(stage: str, dimension: int):
    x = _full_rank(29, dimension)
    record = build_transform(stage, x)
    expected_gram = x.T @ x / x.shape[0]
    expected_lower = torch.linalg.cholesky(expected_gram, upper=False)
    assert torch.equal(record.gram_matrix(), expected_gram)
    assert torch.equal(record.lower_matrix(), expected_lower)
    assert torch.all(torch.diagonal(record.lower_matrix()) > 0)
    assert record.row_count == 29 and record.feature_dim == dimension


def test_column_convention_and_function_space_initialization_are_correct():
    x = _full_rank(37, 5)
    candidates = _full_rank(19, 5)
    beta0 = torch.tensor([0.5, -0.25, 1.25, 0.75, -1.0], dtype=torch.float32)
    record = build_transform("tail", x)
    transformed = transform_features(record, candidates)
    lower = record.lower_matrix()
    assert torch.allclose(lower @ transformed.T, candidates.T, rtol=1e-6, atol=1e-6)
    evidence = pair_initial_coefficients(record, beta0, candidates)
    assert torch.equal(evidence.whitened_beta0, lower.T @ beta0)
    assert torch.allclose(evidence.raw_scores, evidence.whitened_scores, rtol=4e-6, atol=4e-6)
    assert evidence.maximum_absolute_error <= 2e-6


def test_tail_and_root_dimensions_are_strictly_separated():
    tail = build_transform("tail", _full_rank(16, 5))
    root = build_transform("root", _full_rank(16, 7))
    with pytest.raises(ConditioningTransformError, match="dimension mismatch"):
        transform_features(tail, _full_rank(8, 7))
    with pytest.raises(ConditioningTransformError, match="dimension mismatch"):
        transform_features(root, _full_rank(8, 5))
    with pytest.raises(ConditioningTransformError, match="stage/dimension"):
        replace(tail, feature_dim=7).validate()


def test_non_positive_definite_gram_refuses_without_repair(monkeypatch):
    x = torch.ones((20, 5), dtype=torch.float32)
    calls = []
    original = torch.linalg.cholesky

    def observed(input_matrix, *, upper=False, out=None):
        calls.append(input_matrix.detach().clone())
        return original(input_matrix, upper=upper, out=out)

    monkeypatch.setattr(torch.linalg, "cholesky", observed)
    with pytest.raises(ConditioningTransformError, match="not positive definite"):
        build_transform("tail", x)
    assert len(calls) == 1
    assert torch.equal(calls[0], x.T @ x / x.shape[0])


def test_transform_record_is_deterministic_immutable_feature_state():
    x = _full_rank(31, 7)
    first = build_transform("root", x)
    second = build_transform("root", x.clone())
    assert first == second
    assert first.to_bytes() == second.to_bytes()
    assert TransformRecord.from_bytes(first.to_bytes()) == first
    changed_order = build_transform("root", x.flip(0))
    assert changed_order.ordered_design_sha256 != first.ordered_design_sha256
    # G and L can be order-invariant, while binding to ordered X must not be.
    assert changed_order.to_bytes() != first.to_bytes()
    with pytest.raises(Exception):
        first.stage = "tail"


def test_transform_record_rejects_nonpositive_or_nonfinite_diagonal():
    record = build_transform("tail", _full_rank(20, 5))
    lower = record.lower_matrix()
    lower[0, 0] = 0.0
    bad = replace(record, cholesky_lower_fp32_le=b"".join(__import__("struct").pack("<f", value) for value in lower.reshape(-1).tolist()))
    with pytest.raises(ConditioningTransformError, match="positive"):
        bad.validate()


def test_public_transform_apis_cannot_accept_targets_or_outcomes():
    for api in (build_transform, transform_features, pair_initial_coefficients):
        parameters = set(inspect.signature(api).parameters)
        assert not parameters.intersection({"target", "targets", "outcome", "outcomes", "rewards", "oracle_actions"})
    assert set(TransformRecord.__dataclass_fields__) == {
        "schema",
        "stage",
        "row_count",
        "feature_dim",
        "ordered_design_sha256",
        "gram_fp32_le",
        "cholesky_lower_fp32_le",
    }


def test_transform_rejects_wrong_dtype_nonfinite_and_grad_bearing_features():
    with pytest.raises(ConditioningTransformError, match="rank-2 FP32"):
        build_transform("tail", _full_rank(10, 5).double())
    nonfinite = _full_rank(10, 5)
    nonfinite[0, 0] = float("nan")
    with pytest.raises(ConditioningTransformError, match="finite"):
        build_transform("tail", nonfinite)
    with pytest.raises(ConditioningTransformError, match="detached"):
        build_transform("tail", _full_rank(10, 5).requires_grad_())
