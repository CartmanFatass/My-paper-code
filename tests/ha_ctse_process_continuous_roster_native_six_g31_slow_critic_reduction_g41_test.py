from __future__ import annotations

import copy
import hashlib
import io
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import torch

from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process import (
    continuous_roster_native_six_g31_slow_critic_reduction_g41 as g41,
)
from envs.continuous_roster import runtime_capacity as roster_env


ACCEPTED_ANCHOR_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "docs/research/cdc/EVIDENCE_NOTES/fixtures/"
    "CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40/"
    "replicate_0_common_native6_fast_anchor.pt"
)
ACCEPTED_ANCHOR_FIXTURE_BYTES = 81_017
ACCEPTED_ANCHOR_FIXTURE_SHA256 = (
    "d6920e8ab958b776ee0b25a5d2a1b120528b69abc87d4eacc2a6deee2351b521"
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
def accepted_common_anchor() -> Iterator[
    tuple[
        g40.G40NativeSixPolicy,
        g40.AnchoredRosterTrajectory,
        dict[str, object],
    ]
]:
    prior_threads = torch.get_num_threads()
    torch.set_num_threads(1)  # Accepted G39/G40 CPU runtime configuration.
    try:
        fixture_bytes = ACCEPTED_ANCHOR_FIXTURE.read_bytes()
        assert len(fixture_bytes) == ACCEPTED_ANCHOR_FIXTURE_BYTES
        assert hashlib.sha256(fixture_bytes).hexdigest() == (
            ACCEPTED_ANCHOR_FIXTURE_SHA256
        )
        payload = torch.load(
            io.BytesIO(fixture_bytes), map_location="cpu", weights_only=False
        )
        assert isinstance(payload, dict)
        anchor = g41.load_accepted_g40_anchor_checkpoint(
            payload, accepted_anchor_replicate=0
        )
        trajectory = g40.collect_g40_trajectory(
            anchor,
            episode_ids=range(8),
            ledger_seed=10_404_000,
            action_seed=10_405_000,
            device=torch.device("cpu"),
        )
        authority = g41.accepted_g40_anchor_authority(0)
        assert g41._state_digest(anchor.state_dict()) == (
            authority.complete_state_digest
        )
        yield anchor, trajectory, payload
    finally:
        torch.set_num_threads(prior_threads)


def test_static_projection_reconstructs_external_anchor_binding_and_rejects_self_certification(
    accepted_common_anchor: tuple[
        g40.G40NativeSixPolicy,
        g40.AnchoredRosterTrajectory,
        dict[str, object],
    ],
) -> None:
    anchor, _, payload = accepted_common_anchor
    observed_digests = tuple(
        row.complete_state_digest for row in g41.ACCEPTED_G40_ANCHOR_AUTHORITIES
    )
    assert observed_digests == (
        "8868edb01d7ecf93e0832606e5b433522cb9152e75cf972870e94d4116fc5fd6",
        "2c256db95170e3882ef1f257cf5877e20ff74325b4f15592e5d386d0c689b888",
        "8499c8943a965c5b2e7c089a9dddc256e1d195333838c6627ebe0a8720ebde51",
    )
    authority_identity = g41.accepted_g40_anchor_identity(0)
    assert authority_identity["source_manifest"] == (
        "logs/formal_continuous_roster_native_six_credit_reduction_g40_cpu_"
        "20260727_97a8b23_r1/train_manifest.json"
    )
    assert authority_identity["completed_anchor_updates"] == 100
    assert authority_identity["anchor_optimizer_steps"] == 200
    assert payload["completed_anchor_updates"] == 100
    rng_before = torch.random.get_rng_state().clone()
    full, no_slow = g41.project_post_anchor_paths(
        anchor, accepted_anchor_replicate=0
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
    assert certificate["manifest_backed_anchor_authority_valid"] is True
    assert certificate["authority_registry_digests_well_formed"] is True
    assert certificate["checkpoint_state_digest_valid"] is True
    assert certificate["checkpoint_matches_projection"] is True
    assert certificate["standalone_value_output_schema_absent"] is True
    assert certificate["K_search"] == 0
    assert certificate["hypothetical_transitions"] == 0
    assert certificate["maximum_conformance_transitions"] == 384
    checkpoint_authority = checkpoint["accepted_g40_anchor_authority"]
    assert isinstance(checkpoint_authority, dict)
    assert checkpoint_authority["source_commit"] == (
        "97a8b237e0cec6c2713dd2a710d324040fa3dfc2"
    )
    assert checkpoint_authority == authority_identity
    assert checkpoint["standalone_value_output_schema"] is False
    assert not any("slow_critic" in name for name in checkpoint["model_state"])
    assert hasattr(full, "slow_critic")
    assert not hasattr(no_slow, "slow_critic")

    fresh = _anchor()
    fresh_digest = g41._state_digest(fresh.state_dict())
    assert fresh_digest not in {
        row.complete_state_digest for row in g41.ACCEPTED_G40_ANCHOR_AUTHORITIES
    }
    with pytest.raises(TypeError, match="trusted_anchor_digest"):
        g41.project_post_anchor_paths(
            fresh, trusted_anchor_digest=fresh_digest  # type: ignore[call-arg]
        )
    with pytest.raises(ValueError, match="immutable accepted G40 authority"):
        g41.project_post_anchor_paths(fresh, accepted_anchor_replicate=0)
    with pytest.raises(ValueError, match="immutable accepted G40 authority"):
        g41.G41NoSlowProjection(fresh, accepted_anchor_replicate=0)
    with pytest.raises(ValueError, match="not manifest-authorized"):
        g41.project_post_anchor_paths(fresh, accepted_anchor_replicate=3)

    tampered = copy.deepcopy(anchor)
    with torch.no_grad():
        tampered.credit_baselines[2].bias[0].add_(1.0)
    tampered_self_digest = g41._state_digest(tampered.state_dict())
    assert tampered_self_digest != authority_identity["complete_state_digest"]
    with pytest.raises(ValueError, match="immutable accepted G40 authority"):
        g41.project_post_anchor_paths(tampered, accepted_anchor_replicate=0)
    with pytest.raises(ValueError, match="immutable accepted G40 authority"):
        g41.project_post_anchor_paths(anchor, accepted_anchor_replicate=1)

    locally_self_signed_payload = copy.deepcopy(payload)
    locally_self_signed_payload["model_state"] = fresh.state_dict()
    with pytest.raises(ValueError, match="state digest mismatch"):
        g41.load_accepted_g40_anchor_checkpoint(
            locally_self_signed_payload, accepted_anchor_replicate=0
        )
    locally_self_signed_payload["model_state_digest"] = fresh_digest
    with pytest.raises(ValueError, match="payload keys mismatch"):
        g41.load_accepted_g40_anchor_checkpoint(
            locally_self_signed_payload, accepted_anchor_replicate=0
        )
    wrong_exposure_payload = copy.deepcopy(payload)
    wrong_exposure_payload["completed_anchor_updates"] = 200
    with pytest.raises(ValueError, match="checkpoint identity mismatch"):
        g41.load_accepted_g40_anchor_checkpoint(
            wrong_exposure_payload, accepted_anchor_replicate=0
        )

    rewritten = dict(checkpoint)
    rewritten_authority = dict(checkpoint_authority)
    rewritten_authority["complete_state_digest"] = tampered_self_digest
    rewritten["accepted_g40_anchor_authority"] = rewritten_authority
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
    accepted_common_anchor: tuple[
        g40.G40NativeSixPolicy,
        g40.AnchoredRosterTrajectory,
        dict[str, object],
    ],
) -> None:
    anchor, trajectory, _ = accepted_common_anchor
    assert trajectory.rewards.numel() == g41.MAX_CONFORMANCE_TRANSITIONS
    full, no_slow = g41.project_post_anchor_paths(
        anchor, accepted_anchor_replicate=0
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
        roster_env.make_action_noise(
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
