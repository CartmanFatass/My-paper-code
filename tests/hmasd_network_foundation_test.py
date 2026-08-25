import pytest
import torch
from torch import nn

from hmasd.networks import initialize_weights, sparsemax


def _rowwise_sparsemax_reference(logits: torch.Tensor, dim: int) -> torch.Tensor:
    dim = dim if dim >= 0 else logits.ndim + dim
    moved = logits.movedim(dim, -1)
    flat = moved.reshape(-1, moved.shape[-1])
    projected = torch.empty_like(flat)
    support_indices = torch.arange(
        1,
        flat.shape[-1] + 1,
        device=logits.device,
        dtype=logits.dtype,
    )
    for row_index, row in enumerate(flat):
        sorted_row = torch.sort(row, descending=True).values
        cumulative_row = torch.cumsum(sorted_row, dim=0)
        support = 1 + support_indices * sorted_row > cumulative_row
        support_size = int(support.sum().item())
        threshold = (cumulative_row[support_size - 1] - 1) / support_size
        projected[row_index] = torch.clamp(row - threshold, min=0.0)
    return projected.reshape(moved.shape).movedim(-1, dim)


def test_sparsemax_preserves_last_dim_math_and_projects_arbitrary_dim():
    logits = torch.tensor(
        [
            [
                [0.2, -0.1, 0.7, 0.0],
                [1.0, -0.5, 0.3, 0.2],
                [-0.2, 0.4, 0.1, 0.9],
            ],
            [
                [0.5, 0.1, -0.4, 0.6],
                [0.2, 0.8, -0.3, 0.0],
                [0.9, -0.2, 0.4, 0.3],
            ],
        ],
        dtype=torch.float64,
    )

    expected_last = _rowwise_sparsemax_reference(logits, dim=-1)
    actual_last = sparsemax(logits, dim=-1)
    torch.testing.assert_close(actual_last, expected_last, rtol=0.0, atol=1e-15)

    expected_middle = _rowwise_sparsemax_reference(logits, dim=-2)
    actual_middle = sparsemax(logits, dim=-2)
    assert actual_middle.shape == logits.shape
    torch.testing.assert_close(actual_middle, expected_middle, rtol=0.0, atol=1e-15)
    torch.testing.assert_close(
        actual_middle.sum(dim=1),
        torch.ones_like(actual_middle.sum(dim=1)),
        rtol=0.0,
        atol=1e-12,
    )
    assert torch.all(actual_middle >= 0)


def test_sparsemax_vectorizes_batch_without_host_scalar_sync(monkeypatch):
    logits = torch.randn(8, 5, dtype=torch.float32)
    original_sort = torch.sort
    sort_calls = 0

    def counted_sort(*args, **kwargs):
        nonlocal sort_calls
        sort_calls += 1
        return original_sort(*args, **kwargs)

    def forbidden_item(*_args, **_kwargs):
        raise AssertionError("sparsemax must not synchronize a support index to the host")

    monkeypatch.setattr(torch, "sort", counted_sort)
    monkeypatch.setattr(torch.Tensor, "item", forbidden_item)

    projected = sparsemax(logits, dim=-1)

    assert sort_calls == 1
    assert projected.shape == logits.shape


def test_sparsemax_keeps_input_storage_and_autograd_flow_pure():
    logits = torch.randn(2, 3, 4, dtype=torch.float64, requires_grad=True)
    input_before = logits.detach().clone()

    projected = sparsemax(logits, dim=1)
    weights = torch.linspace(
        -0.7,
        0.9,
        projected.numel(),
        dtype=projected.dtype,
    ).reshape_as(projected)
    (projected * weights).sum().backward()

    assert projected.dtype == logits.dtype
    assert projected.device == logits.device
    assert torch.equal(logits.detach(), input_before)
    assert logits.grad is not None
    assert torch.isfinite(logits.grad).all()

    gradcheck_logits = torch.tensor(
        [[0.3, -0.1, 0.2], [0.1, 0.2, -0.2]],
        dtype=torch.float64,
        requires_grad=True,
    )
    assert torch.autograd.gradcheck(
        lambda value: sparsemax(value, dim=-2),
        (gradcheck_logits,),
        eps=1e-6,
        atol=1e-5,
        rtol=1e-4,
    )
    with pytest.raises(TypeError):
        sparsemax(gradcheck_logits, dim=0.5)


def test_sparsemax_is_stable_for_large_finite_translations():
    logits = torch.tensor(
        [[1.0e20, 1.0e20], [1.0e20, 1.0e20]],
        dtype=torch.float32,
    )

    projected = sparsemax(logits, dim=-1)

    assert torch.equal(projected, torch.full_like(logits, 0.5))
    assert torch.equal(projected.sum(dim=-1), torch.ones(2, dtype=logits.dtype))


def test_initialize_weights_honors_zero_gain_and_tracks_parameter_mutation():
    module = nn.Sequential(nn.Linear(3, 4), nn.Tanh(), nn.Linear(4, 2))
    last_weight_grad = torch.full_like(module[-1].weight, 7.0)
    module[-1].weight.grad = last_weight_grad.clone()

    initialize_weights(module, gain=1.0, last_layer_gain=0.0)

    assert torch.count_nonzero(module[0].weight) > 0
    assert torch.count_nonzero(module[-1].weight) == 0
    assert torch.count_nonzero(module[-1].bias) == 0
    assert torch.equal(module[-1].weight.grad, last_weight_grad)

    linear = nn.Linear(3, 2, bias=False)
    inputs = torch.randn(4, 3, requires_grad=True)
    stale_output = linear(inputs).square().sum()
    version_before = linear.weight._version

    initialize_weights(linear, gain=0.5)

    assert linear.weight._version > version_before
    with pytest.raises(RuntimeError, match="modified by an inplace operation"):
        stale_output.backward()


def test_initialize_weights_applies_single_head_gain_and_embedding_initialization():
    head = nn.Linear(4, 2)
    initialize_weights(head, gain=1.0, last_layer_gain=0.01)
    torch.testing.assert_close(
        head.weight @ head.weight.T,
        torch.eye(2, dtype=head.weight.dtype) * 1.0e-4,
        rtol=1.0e-5,
        atol=1.0e-7,
    )

    embedding = nn.Embedding(3, 4, padding_idx=1)
    with torch.no_grad():
        embedding.weight.fill_(3.0)
    initialize_weights(embedding, gain=0.5)
    assert torch.count_nonzero(embedding.weight[embedding.padding_idx]) == 0
    assert torch.count_nonzero(embedding.weight[0]) > 0
    assert torch.count_nonzero(embedding.weight[2]) > 0
