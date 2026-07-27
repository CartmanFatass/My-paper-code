from __future__ import annotations

import copy
from collections.abc import Iterator
from typing import Any

import pytest
import torch

from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process import (
    continuous_roster_native_six_g31_slow_critic_reduction_g41 as g41,
)


TRUSTED_PROOF_ANCHOR_DIGEST = (
    "1037eedea543ff2eb5c04d45df1367b1dc8ea19cde939c80af2ac6fc54c23931"
)


def _optimizer_state(
    optimizer: torch.optim.Optimizer,
) -> tuple[tuple[tuple[str, Any], ...], ...]:
    rows: list[tuple[tuple[str, Any], ...]] = []
    for group in optimizer.param_groups:
        for parameter in group["params"]:
            state = optimizer.state[parameter]
            rows.append(
                tuple(
                    (
                        name,
                        value.detach().clone()
                        if isinstance(value, torch.Tensor)
                        else value,
                    )
                    for name, value in sorted(state.items())
                )
            )
    return tuple(rows)


def _assert_optimizer_state_equal(
    left: torch.optim.Optimizer, right: torch.optim.Optimizer
) -> None:
    left_rows, right_rows = _optimizer_state(left), _optimizer_state(right)
    assert len(left_rows) == len(right_rows)
    for left_state, right_state in zip(left_rows, right_rows):
        assert tuple(name for name, _ in left_state) == tuple(
            name for name, _ in right_state
        )
        for (_, left_value), (_, right_value) in zip(left_state, right_state):
            if isinstance(left_value, torch.Tensor):
                assert isinstance(right_value, torch.Tensor)
                assert torch.equal(left_value, right_value)
            else:
                assert left_value == right_value


def _anchor() -> g40.G40NativeSixPolicy:
    return g40.make_model(8, initialization_seed=10_401_000)


@pytest.fixture(scope="module")
def trusted_common_anchor() -> Iterator[
    tuple[g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory]
]:
    prior_threads = torch.get_num_threads()
    torch.set_num_threads(1)  # Accepted G39/G40 CPU runtime configuration.
    try:
        anchor = _anchor()
        trajectory = g40.collect_g40_trajectory(
            anchor,
            episode_ids=range(8),
            ledger_seed=10_404_000,
            action_seed=10_405_000,
            device=torch.device("cpu"),
        )
        optimizer = torch.optim.Adam(
            anchor.actor_credit_parameters(),
            lr=g40.LEARNING_RATE,
            betas=(0.9, 0.999),
            eps=1e-8,
            weight_decay=0.0,
        )
        g40.optimize_common_fast_anchor_update(
            anchor, optimizer, trajectory, ppo_passes=2
        )
        del optimizer
        assert g41._state_digest(anchor.state_dict()) == TRUSTED_PROOF_ANCHOR_DIGEST
        yield anchor, trajectory
    finally:
        torch.set_num_threads(prior_threads)


def test_static_projection_reconstructs_external_anchor_binding_and_rejects_self_certification(
    trusted_common_anchor: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, _ = trusted_common_anchor
    rng_before = torch.random.get_rng_state().clone()
    full, no_slow = g41.project_post_anchor_paths(
        anchor, trusted_anchor_digest=TRUSTED_PROOF_ANCHOR_DIGEST
    )
    assert torch.equal(rng_before, torch.random.get_rng_state())
    full.begin_credit_branch_phase()
    no_slow.begin_credit_branch_phase()
    full_optimizer = g41.make_actor_head_optimizer(full)
    no_slow_optimizer = g41.make_actor_head_optimizer(no_slow)
    checkpoint = g41.build_projected_checkpoint(no_slow)
    certificate = g41.reconstruct_static_certificate(
        anchor,
        full,
        no_slow,
        full_optimizer,
        no_slow_optimizer,
        checkpoint,
        trusted_anchor_digest=TRUSTED_PROOF_ANCHOR_DIGEST,
    )
    assert certificate["passed"] is True, certificate
    assert all(certificate["zero_standalone_slow_reads"].values())
    assert certificate[
        "no_standalone_slow_module_parameter_or_checkpoint_key"
    ] is True
    assert certificate["actor_head_parameter_contract_equal"] is True
    assert certificate["actor_head_optimizer_order_equal"] is True
    assert certificate["actor_head_optimizer_states_empty_and_separate"] is True
    assert certificate["retained_state_bytes_equal"] is True
    assert certificate["retained_storage_disjoint"] is True
    assert certificate["standalone_slow_retained_storage_disjoint"] is True
    assert certificate["projection_rng_unchanged"] is True
    assert certificate[
        "checkpoint_bound_to_accepted_g40_source_and_anchor"
    ] is True
    assert certificate["trusted_anchor_digest_well_formed"] is True
    assert certificate["checkpoint_state_digest_valid"] is True
    assert certificate["checkpoint_matches_projection"] is True
    assert certificate["standalone_value_output_schema_absent"] is True
    assert certificate["K_search"] == 0
    assert certificate["hypothetical_transitions"] == 0
    assert certificate["maximum_conformance_transitions"] == 384
    assert checkpoint["accepted_g40_source_commit"] == (
        "97a8b237e0cec6c2713dd2a710d324040fa3dfc2"
    )
    assert checkpoint["standalone_value_output_schema"] is False
    assert not any("slow_critic" in name for name in checkpoint["model_state"])
    assert hasattr(full, "slow_critic")
    assert not hasattr(no_slow, "slow_critic")

    fresh = _anchor()
    fresh_digest = g41._state_digest(fresh.state_dict())
    assert fresh_digest != TRUSTED_PROOF_ANCHOR_DIGEST
    with pytest.raises(ValueError, match="lowercase SHA-256"):
        g41.project_post_anchor_paths(
            fresh, trusted_anchor_digest="not-a-trusted-checkpoint-digest"
        )
    with pytest.raises(ValueError, match="externally trusted digest"):
        g41.project_post_anchor_paths(
            fresh, trusted_anchor_digest=TRUSTED_PROOF_ANCHOR_DIGEST
        )

    tampered = copy.deepcopy(anchor)
    with torch.no_grad():
        tampered.credit_baselines[2].bias[0].add_(1.0)
    tampered_self_digest = g41._state_digest(tampered.state_dict())
    assert tampered_self_digest != TRUSTED_PROOF_ANCHOR_DIGEST
    with pytest.raises(ValueError, match="externally trusted digest"):
        g41.project_post_anchor_paths(
            tampered, trusted_anchor_digest=TRUSTED_PROOF_ANCHOR_DIGEST
        )

    rewritten = dict(checkpoint)
    rewritten["accepted_g40_anchor_state_digest"] = tampered_self_digest
    rewritten["model_state_digest"] = g41._state_digest(
        rewritten["model_state"]
    )
    rewritten_certificate = g41.reconstruct_static_certificate(
        tampered,
        full,
        no_slow,
        full_optimizer,
        no_slow_optimizer,
        rewritten,
        trusted_anchor_digest=TRUSTED_PROOF_ANCHOR_DIGEST,
    )
    assert rewritten_certificate["passed"] is False
    assert rewritten_certificate[
        "checkpoint_bound_to_accepted_g40_source_and_anchor"
    ] is False
    assert rewritten_certificate["checkpoint_state_digest_valid"] is True
    assert rewritten_certificate["checkpoint_matches_projection"] is True


def test_g31_credit_targets_are_exact_and_have_no_slow_value_input() -> None:
    rewards = torch.tensor([[1.0], [2.0], [3.0]])
    immediate = torch.tensor([[0.1], [0.2], [0.3]])
    successor = torch.tensor([[0.4], [0.5], [0.6]])
    terminals = torch.tensor([[False], [False], [True]])
    reduced = g41.compute_g31_credit_without_slow(
        rewards=rewards,
        immediate_baselines=immediate,
        successor_baselines=successor,
        terminals=terminals,
    )
    full_left = g40.compute_credit_targets(
        rewards=rewards,
        slow_values=torch.zeros_like(rewards),
        immediate_baselines=immediate,
        successor_baselines=successor,
        terminals=terminals,
    )
    full_right = g40.compute_credit_targets(
        rewards=rewards,
        slow_values=torch.full_like(rewards, 37.0),
        immediate_baselines=immediate,
        successor_baselines=successor,
        terminals=terminals,
    )
    for full in (full_left, full_right):
        assert torch.equal(reduced.returns, full.returns)
        assert torch.equal(reduced.successor_targets, full.successor_targets)
        assert torch.equal(reduced.immediate_advantage, full.immediate_advantage)
        assert torch.equal(reduced.successor_advantage, full.successor_advantage)


def test_one_cpp_batch_two_passes_is_bitwise_full_no_slow_and_g40_equivalent(
    trusted_common_anchor: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, trajectory = trusted_common_anchor
    assert trajectory.rewards.numel() == g41.MAX_CONFORMANCE_TRANSITIONS
    full, no_slow = g41.project_post_anchor_paths(
        anchor, trusted_anchor_digest=TRUSTED_PROOF_ANCHOR_DIGEST
    )
    full.begin_credit_branch_phase()
    no_slow.begin_credit_branch_phase()
    reference = copy.deepcopy(full)

    full_actor = g41.make_actor_head_optimizer(full)
    no_slow_actor = g41.make_actor_head_optimizer(no_slow)
    reference_actor = g41.make_actor_head_optimizer(reference)
    full_slow = g41.make_full_slow_optimizer(full)
    reference_slow = g41.make_full_slow_optimizer(reference)

    checkpoint = g41.build_projected_checkpoint(no_slow)
    certificate = g41.reconstruct_static_certificate(
        anchor,
        full,
        no_slow,
        full_actor,
        no_slow_actor,
        checkpoint,
        trusted_anchor_digest=TRUSTED_PROOF_ANCHOR_DIGEST,
    )
    assert certificate["passed"] is True, certificate

    rng_before = torch.random.get_rng_state().clone()
    reference_metrics = g40.optimize_credit_branch_update(
        g40.G31_ARM,
        reference,
        reference_actor,
        reference_slow,
        trajectory,
        ppo_passes=2,
    )
    full_metrics = g41.optimize_retained_actor_head_update(
        full, full_actor, trajectory, ppo_passes=2
    )
    no_slow_metrics = g41.optimize_retained_actor_head_update(
        no_slow, no_slow_actor, trajectory, ppo_passes=2
    )
    slow_metrics = g41.optimize_full_slow_critic_update(
        full, full_slow, trajectory, ppo_passes=2
    )
    assert torch.equal(rng_before, torch.random.get_rng_state())
    assert full_metrics == no_slow_metrics
    assert full_metrics["actor_head_optimizer_steps"] == 2
    assert slow_metrics["slow_critic_optimizer_steps"] == 2
    assert reference_metrics["actor_optimizer_steps"] == 2.0
    assert reference_metrics["slow_critic_optimizer_steps"] == 2.0

    full_named = dict(full.named_parameters())
    no_slow_named = dict(no_slow.named_parameters())
    for name in g41.actor_head_parameter_names(full):
        assert torch.equal(full_named[name], no_slow_named[name]), name
    assert torch.equal(full.log_std, no_slow.log_std)
    assert g40.state_bytes(full.credit_baselines) == g40.state_bytes(
        no_slow.credit_baselines
    )
    _assert_optimizer_state_equal(full_actor, no_slow_actor)

    assert g40.state_bytes(full) == g40.state_bytes(reference)
    _assert_optimizer_state_equal(full_actor, reference_actor)
    _assert_optimizer_state_equal(full_slow, reference_slow)

    noise = torch.as_tensor(
        g40.g32.make_action_noise(
            range(8), action_seed=10_405_000, member_capacity=8
        )[0]
    )
    forward = g41.forward_equality_audit(
        full,
        no_slow,
        observations=trajectory.observations[0],
        active_mask=trajectory.active_mask[0],
        critic_state=trajectory.critic_states[0],
        hidden=trajectory.hidden_before[0],
        sampling_noise=noise,
    )
    assert forward["passed"] is True, forward
    assert max(forward["maximum_errors"].values()) == 0.0

    full_replay = g41.retained_replay(full, trajectory)
    no_slow_replay = g41.retained_replay(no_slow, trajectory)
    for name in (
        "log_probs",
        "entropies",
        "immediate_baselines",
        "successor_baselines",
        "hidden_after",
        "prefix_action_sums",
        "active_mask",
    ):
        assert torch.equal(getattr(full_replay, name), getattr(no_slow_replay, name))
    trace = g40.branch_trajectory_match(trajectory, trajectory)
    assert trace["errors"]["rewards"] <= 1e-7
    assert trace["passed"] is True
