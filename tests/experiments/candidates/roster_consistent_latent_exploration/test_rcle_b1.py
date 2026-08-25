from __future__ import annotations

import numpy as np
import pytest

from experiments.candidates.roster_consistent_latent_exploration.authorization import ProductionPermit
from experiments.candidates.roster_consistent_latent_exploration.certificate import build_certificate
from experiments.candidates.roster_consistent_latent_exploration.config import REGISTERED
from experiments.candidates.roster_consistent_latent_exploration.host import (
    Roster,
    evaluate_actions,
    relative_bins,
    roster_accepted,
    scripted_codebook_actions,
)
from experiments.candidates.roster_consistent_latent_exploration.models import Actor, Posterior, actor_inputs
from experiments.candidates.roster_consistent_latent_exploration.resources import resource_proposal
from experiments.candidates.roster_consistent_latent_exploration.rng import generator
from experiments.candidates.roster_consistent_latent_exploration.runner import _rss_bytes
from experiments.candidates.roster_consistent_latent_exploration.training import BlockData, _rollout


def test_exact_deterministic_preactivity_certificate() -> None:
    certificate = build_certificate()
    assert certificate["passed"], certificate
    assert certificate["registered_stochastic_object_materialized"] is False
    assert "certificate.py" in certificate["source_sha256"]


@pytest.mark.parametrize("n", (4, 8, 12))
def test_handwritten_host_codebook_and_row_permutation(n: int) -> None:
    x = np.tile(np.asarray((0.1, 0.4, 0.6, 0.9)), n // 4)
    bins = relative_bins(x, 0.5)
    assert roster_accepted(bins)
    a1, a2 = scripted_codebook_actions(bins, 3)
    original = evaluate_actions(bins, a1, a2, 3)
    order = np.arange(n - 1, -1, -1)
    moved = evaluate_actions(bins[order], a1[order], a2[order], 3)
    assert original.valid and original.winning_rotation == 3 and original.reward == 1
    assert moved.valid and moved.winning_rotation == 3 and moved.reward == 1
    assert np.array_equal(original.fractions, moved.fractions)


def test_exact_model_shape_and_actor_inputs() -> None:
    actor = Actor()
    posterior = Posterior()
    assert sum(parameter.numel() for parameter in actor.parameters()) == 1506
    assert sum(parameter.numel() for parameter in posterior.parameters()) == 16
    x = np.asarray((0.1, 0.4, 0.6, 0.9))
    assert actor_inputs(x, 0.5, 2, 1).shape == (4, 11)
    assert actor_inputs(x, 0.5, 2, 2, np.asarray((0, 1, 0, 1))).shape == (4, 11)


def test_registered_rng_requires_unforgeable_production_permit() -> None:
    with pytest.raises(PermissionError):
        ProductionPermit(object(), None, None, {})
    with pytest.raises(PermissionError):
        generator(object(), "fixture")


@pytest.mark.parametrize("arm", ("RCLE", "COMMON-Z", "SHUFFLED-MI", "INDEPENDENT-ENTROPY"))
def test_handwritten_invalid_rollout_never_supplies_posterior_symbol(arm: str) -> None:
    x = np.asarray((0.1, 0.4, 0.6, 0.9), dtype=np.float64)
    roster = Roster(
        xi=0.5, x=x, mu=0.5, bins=relative_bins(x, 0.5),
        row_permutation=np.arange(4), proposal_count=1,
    )
    block = BlockData(
        n=4,
        roster=roster,
        locks=np.repeat(np.arange(4), 4),
        probe_latents=np.tile(np.arange(4), 4),
        private_latents=np.tile(np.arange(4), (16, 1)),
        shuffled_labels=np.tile(np.arange(4), 4),
        action_uniforms=np.full((2, 16, 4), 0.25, dtype=np.float64),
    )
    result = _rollout(Actor(), Posterior(), arm, block)
    assert not result["valid"].any()
    assert result["invalid_posterior_symbols"] == 0
    assert result["posterior_terms"].detach().abs().sum().item() == 0.0
    (-result["posterior_terms"].mean()).backward()


@pytest.mark.parametrize("arm", ("RCLE", "SHUFFLED-MI", "INDEPENDENT-ENTROPY"))
def test_handwritten_valid_rollout_has_finite_actor_and_posterior_paths(arm: str) -> None:
    roster = Roster(
        xi=0.5, x=np.full(4, 0.5), mu=0.5, bins=np.zeros(4, dtype=np.int64),
        row_permutation=np.arange(4), proposal_count=1,
    )
    block = BlockData(
        n=4, roster=roster, locks=np.zeros(16, dtype=np.int64),
        probe_latents=np.tile(np.arange(4), 4),
        private_latents=np.tile(np.arange(4), (16, 1)),
        shuffled_labels=np.tile(np.arange(4), 4),
        action_uniforms=np.full((2, 16, 4), 0.25, dtype=np.float64),
    )
    actor, posterior = Actor(), Posterior()
    result = _rollout(actor, posterior, arm, block)
    assert result["valid"].all()
    actor_objective = -result["log_probability"].mean()
    if arm == "INDEPENDENT-ENTROPY":
        actor_objective -= REGISTERED.alpha * result["route_entropy"].mean()
    actor_objective.backward()
    assert all(parameter.grad is not None for parameter in actor.parameters())
    (-result["posterior_terms"].mean()).backward()
    assert posterior.logits.grad is not None


def test_literal_workload_counts() -> None:
    proposal = resource_proposal()
    assert proposal["training_episodes"] == 3_072_000
    assert proposal["ordinary_evaluation_episodes"] == 1_179_648
    assert proposal["cut_episodes"] == 589_824
    assert proposal["total_registered_episodes"] <= REGISTERED.max_episodes


def test_windows_resource_observer_returns_positive_rss() -> None:
    assert _rss_bytes() > 0
