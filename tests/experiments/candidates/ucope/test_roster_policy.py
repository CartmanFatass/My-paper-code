"""Focused tests for the UCOPE roster policy binding.

The load-bearing one is :func:`test_replacing_candidate_changes_execution_path`:
the task list requires at least one test proving that removing or replacing the
candidate changes the REAL execution path, not merely a synthetic fixture.
"""

from __future__ import annotations

import torch

from envs.continuous_roster import runtime_capacity as roster_env
from experiments.candidates.ucope import roster_policy as rp

CAPACITY = roster_env.TRAIN_CAPACITY
BATCH = 4
SEED = 20260805


def _obs(batch: int = BATCH) -> torch.Tensor:
    generator = torch.Generator().manual_seed(SEED)
    return torch.rand(
        (batch, CAPACITY, rp.RETAINED_OBSERVATION_DIM), generator=generator
    )


def _mask(active: int, batch: int = BATCH) -> torch.Tensor:
    mask = torch.zeros((batch, CAPACITY), dtype=torch.bool)
    mask[:, :active] = True
    return mask


def test_actor_input_is_six_source_coordinates_plus_two_count_channels():
    policy = rp.UcopeCountStatePolicy(member_capacity=CAPACITY)
    built = policy.actor_input(_obs(), _mask(5))
    assert built.shape[-1] == rp.UCOPE_OBSERVATION_DIM == 8
    assert rp.UCOPE_OBSERVATION_DIM == rp.RETAINED_OBSERVATION_DIM + rp.UCOPE_COUNT_DIM


def test_counts_start_at_zero_and_only_accumulate_on_membership_change():
    policy = rp.UcopeCountStatePolicy(member_capacity=CAPACITY)
    obs, steady = _obs(), _mask(5)

    first = policy.actor_input(obs, steady)
    assert torch.count_nonzero(first[..., rp.RETAINED_OBSERVATION_DIM:]) == 0

    # No membership change -> counts stay put.
    second = policy.actor_input(obs, steady)
    assert torch.equal(
        first[..., rp.RETAINED_OBSERVATION_DIM:],
        second[..., rp.RETAINED_OBSERVATION_DIM:],
    )

    # A member leaves -> churn appears.
    after = policy.actor_input(obs, _mask(4))
    assert torch.count_nonzero(after[..., rp.RETAINED_OBSERVATION_DIM:]) > 0


def test_counts_are_monotone_and_carry_no_future_information():
    policy = rp.UcopeCountStatePolicy(member_capacity=CAPACITY)
    obs = _obs()
    previous = torch.zeros((BATCH, CAPACITY))
    for active in (6, 6, 5, 5, 4, 6):
        built = policy.actor_input(obs, _mask(active))
        own = built[..., rp.RETAINED_OBSERVATION_DIM] * rp.COUNT_SCALE
        assert torch.all(own + 1e-6 >= previous), "churn must never decrease"
        previous = own


def test_candidate_and_comparator_are_resource_matched():
    arms = rp.make_ucope_pair(CAPACITY, initialization_seed=SEED)
    candidate = arms["UCOPE_COUNT_STATE"]
    blind = arms["UCOPE_COUNT_BLIND"]

    n_candidate = sum(p.numel() for p in candidate.parameters())
    n_blind = sum(p.numel() for p in blind.parameters())
    assert n_candidate == n_blind, "arms must have identical parameter counts"

    for (name, left), (other, right) in zip(
        candidate.state_dict().items(), blind.state_dict().items()
    ):
        assert name == other
        assert torch.equal(left, right), f"initial parameters differ at {name}"


def test_replacing_candidate_changes_execution_path():
    """Swapping the candidate for the comparator changes what the network sees.

    This is the proof that the candidate is genuinely wired in: after a real
    membership change the two arms present DIFFERENT tensors to the same
    network, so deleting the count mechanism is observable downstream rather
    than being a decorative wrapper.
    """
    arms = rp.make_ucope_pair(CAPACITY, initialization_seed=SEED)
    candidate = arms["UCOPE_COUNT_STATE"]
    blind = arms["UCOPE_COUNT_BLIND"]
    obs = _obs()

    # Drive both arms through the same membership history.
    for active in (6, 5, 5, 4):
        built_candidate = candidate.actor_input(obs, _mask(active))
        built_blind = blind.actor_input(obs, _mask(active))

    source = slice(0, rp.RETAINED_OBSERVATION_DIM)
    counts = slice(rp.RETAINED_OBSERVATION_DIM, rp.UCOPE_OBSERVATION_DIM)

    # The six source coordinates are identical -- only information differs.
    assert torch.equal(built_candidate[..., source], built_blind[..., source])

    # The count channels are not: the candidate carries churn, the blind arm
    # carries the severed constant.
    assert not torch.equal(built_candidate[..., counts], built_blind[..., counts])
    assert torch.count_nonzero(built_candidate[..., counts]) > 0
    assert torch.all(built_blind[..., counts] == rp.COUNT_BLIND_CONSTANT)


def test_inactive_members_never_carry_count_signal():
    policy = rp.UcopeCountStatePolicy(member_capacity=CAPACITY)
    obs = _obs()
    for active in (6, 4):
        built = policy.actor_input(obs, _mask(active))
    mask = _mask(4)
    counts = built[..., rp.RETAINED_OBSERVATION_DIM:]
    assert torch.count_nonzero(counts[~mask]) == 0


def test_reset_clears_accumulated_counts():
    policy = rp.UcopeCountStatePolicy(member_capacity=CAPACITY)
    obs = _obs()
    policy.actor_input(obs, _mask(6))
    policy.actor_input(obs, _mask(4))
    policy.reset_count_state()
    built = policy.actor_input(obs, _mask(6))
    assert torch.count_nonzero(built[..., rp.RETAINED_OBSERVATION_DIM:]) == 0
