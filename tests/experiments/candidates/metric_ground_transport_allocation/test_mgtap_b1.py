from __future__ import annotations

import numpy as np
import torch

from experiments.candidates.metric_ground_transport_allocation.actor import Actor, HADAMARD, metric_map
from experiments.candidates.metric_ground_transport_allocation.analysis import _equivalence, _positive
from experiments.candidates.metric_ground_transport_allocation.certificate import deterministic_certificate
from experiments.candidates.metric_ground_transport_allocation.config import EXPECTED_COUNTS, demand, workload_counts
from experiments.candidates.metric_ground_transport_allocation.decoder import decode
from experiments.candidates.metric_ground_transport_allocation.environment import canonical_roles, coupling_from_actions, feasibility_residuals, reward
from experiments.candidates.metric_ground_transport_allocation.oracle import canonical_oracle
from experiments.candidates.metric_ground_transport_allocation.run import _peak_rss_bytes


def test_workload_counts_are_literal() -> None:
    assert workload_counts() == EXPECTED_COUNTS


def test_maps_are_invertible_and_exactly_equal_class() -> None:
    w = np.arange(48, dtype=np.float64).reshape(8, 6) / 13.0
    assert np.allclose(HADAMARD.T @ HADAMARD, np.eye(8), atol=1e-14)
    for binding in ("INTACT", "CUT"):
        metric = metric_map(binding)
        free = HADAMARD.T @ metric @ w
        assert np.allclose(metric @ w, HADAMARD @ free, atol=1e-13)
        assert np.linalg.eigvalsh(metric).min() >= 0.5 - 1e-12


def test_handwritten_decoder_is_legal_and_row_equivariant() -> None:
    actor = Actor("METRIC", "INTACT")
    with torch.no_grad():
        actor.W.copy_(torch.arange(48, dtype=torch.float64).reshape(8, 6) / 47.0)
    feature = torch.tensor([[1.0, 0.5, 0.0, 0.0, 0.5, 0.0]], dtype=torch.float64)
    roles = np.asarray([canonical_roles(4)])
    demands = np.asarray([[2, 0, 0, 2]])
    ranks = np.asarray([[2, 0, 3, 1]])
    uniforms = np.asarray([[0.11, 0.37, 0.71, 0.93]])
    _, mapped, idle = actor.scores(feature)
    base = decode(mapped, idle, torch.as_tensor(roles), torch.as_tensor(demands), torch.as_tensor(ranks), torch.as_tensor(uniforms))
    permutation = np.asarray([[2, 0, 3, 1]])
    moved_roles = np.take_along_axis(roles, permutation, axis=1)
    moved_ranks = np.take_along_axis(ranks, permutation, axis=1)
    replay = decode(mapped, idle, torch.as_tensor(moved_roles), torch.as_tensor(demands), torch.as_tensor(moved_ranks), torch.as_tensor(uniforms))
    restored = np.empty_like(replay.actions.numpy())
    np.put_along_axis(restored, permutation, replay.actions.numpy(), axis=1)
    assert np.array_equal(restored, base.actions.numpy())
    x, idle_action, unmet = coupling_from_actions(base.actions.numpy(), demands)
    assert not np.any(feasibility_residuals(x, idle_action, unmet, demands))
    assert torch.isfinite(base.log_probability).all()
    assert torch.isfinite(base.mean_entropy).all()


def test_oracle_is_canonical_and_feasible() -> None:
    result = canonical_oracle(4, demand(4, (0, 3), "SLACK", 1))
    assert result["role_task_counts"].shape == (2, 4)
    assert result["role_idle_counts"].sum() + result["role_task_counts"].sum() == 4
    assert np.array_equal(result["role_task_counts"].sum(axis=0) + result["unmet_counts"], np.asarray((2, 0, 0, 2)))


def test_reward_is_exactly_row_permutation_invariant() -> None:
    roles = np.asarray([[0, 0, 1, 1, 0, 1]])
    actions = np.asarray([[0, 1, 2, 3, 4, 2]])
    unmet = np.asarray([[1, 0, 2, 0]])
    permutation = np.asarray([[5, 2, 0, 4, 1, 3]])
    moved_roles = np.take_along_axis(roles, permutation, axis=1)
    moved_actions = np.take_along_axis(actions, permutation, axis=1)
    assert np.array_equal(reward(roles, actions, unmet), reward(moved_roles, moved_actions, unmet))


def test_interval_status_boundaries_are_literal() -> None:
    assert _positive({"lower": 0.021, "upper": 0.03}, 0.02) == "SUPPORTED_POSITIVE"
    assert _positive({"lower": 0.0, "upper": 0.02}, 0.02) == "AFFIRMATIVELY_BELOW_MATERIAL"
    assert _positive({"lower": 0.0, "upper": 0.03}, 0.02) == "POSITIVE_UNRESOLVED"
    assert _equivalence({"lower": -0.02, "upper": 0.02}, 0.02) == "EQUIVALENT"
    assert _equivalence({"lower": 0.021, "upper": 0.03}, 0.02) == "AFFIRMATIVELY_OUTSIDE_EQUIVALENCE"


def test_full_deterministic_preactivity_certificate() -> None:
    certificate, tables, lookup = deterministic_certificate()
    assert certificate["passed"], certificate
    assert len(lookup) == 192
    assert tables["oracle_role_task_counts"].shape == (192, 2, 4)


def test_resource_observer_returns_positive_rss() -> None:
    assert _peak_rss_bytes() > 0
