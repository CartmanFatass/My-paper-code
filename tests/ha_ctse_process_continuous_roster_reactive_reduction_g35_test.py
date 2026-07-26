from __future__ import annotations

import numpy as np
import pytest
import torch

from ha_ctse_process import continuous_roster_reactive_reduction_g35 as g35
from ha_ctse_process import runtime_capacity_continuous_roster_g32 as g32
from ha_ctse_process.anchored_residual_g19 import attach_credit_baselines


def _paired() -> dict[str, g35.G35MatchedStateCarryPolicy]:
    return g35.make_paired_models(8, initialization_seed=10_351_000)


def test_matched_arms_have_identical_parameters_and_only_carry_differs() -> None:
    models = _paired()
    rec, cs = models[g35.REC_ARM], models[g35.CS_ARM]
    g35.assert_parameter_match(rec, cs, require_byte_identity=True)
    assert rec.carry_mode == "REC"
    assert cs.carry_mode == "CS"
    assert "carry_mode" not in rec.state_dict()
    assert tuple(rec.state_dict()) == tuple(cs.state_dict())
    assert torch.count_nonzero(rec.current_readout.weight) == 0
    assert torch.count_nonzero(cs.current_readout.bias) == 0

    encoded = torch.randn(3, g35.HIDDEN_DIM)
    stored = torch.randn(3, g35.HIDDEN_DIM)
    rec_actor = rec.policy
    cs_actor = cs.policy
    assert isinstance(rec_actor, g35.G35MatchedStateCarryActor)
    assert isinstance(cs_actor, g35.G35MatchedStateCarryActor)
    assert torch.equal(rec_actor._actor_hidden_input(encoded, stored), encoded + stored)
    assert torch.equal(cs_actor._actor_hidden_input(encoded, stored), encoded)
    assert torch.equal(rec_actor._carried_hidden(stored), stored)
    assert torch.count_nonzero(cs_actor._carried_hidden(stored)) == 0


def test_forced_initial_state_is_equal_and_cs_storage_remains_zero() -> None:
    models = _paired()
    ledgers = tuple(
        g32.make_ledger(
            episode,
            master_seed=10_357_000,
            profile=g32.TRAIN_PROFILES[episode % len(g32.TRAIN_PROFILES)],
        )
        for episode in range(2)
    )
    views = tuple(g32.RuntimeCapacityRosterEnv(row).observe() for row in ledgers)
    noise = torch.as_tensor(
        g32.make_action_noise(range(2), action_seed=10_357_000, member_capacity=8)[0]
    )
    errors = g35.forced_initial_equality(
        models[g35.REC_ARM],
        models[g35.CS_ARM],
        observations=torch.as_tensor(np.stack([row.observations for row in views])),
        active_mask=torch.as_tensor(np.stack([row.active_mask for row in views])),
        critic_state=torch.as_tensor(np.stack([row.critic_state for row in views])),
        sampling_noise=noise,
    )
    assert max(errors.values()) <= g35.INITIAL_EQUALITY_TOLERANCE

    cs_trajectory = g32.collect_trajectory(
        models[g35.CS_ARM],
        episode_ids=range(2),
        ledger_seed=10_357_000,
        action_seed=10_357_000,
        device=torch.device("cpu"),
    )
    assert torch.count_nonzero(cs_trajectory.hidden_before) == 0
    assert torch.count_nonzero(cs_trajectory.hidden_after) == 0


def test_live_gradient_audit_uses_every_registered_group() -> None:
    models = _paired()
    expected = {
        "member_encoder",
        "context_encoder",
        "gated_cell_input_weights",
        "gated_cell_recurrent_weights",
        "gated_cell_biases",
        "action_head",
        "current_readout",
        "log_std",
        "centralized_slow_critic",
        "immediate_baseline",
        "successor_baseline",
    }
    for arm, model in models.items():
        raw = g32.collect_trajectory(
            model,
            episode_ids=range(8),
            ledger_seed=10_357_000,
            action_seed=10_357_000,
            device=torch.device("cpu"),
        )
        trajectory = attach_credit_baselines(model, raw, device=torch.device("cpu"))
        audit = g35.g35_initial_gradient_audit(model, trajectory, gamma=0.99)
        assert audit.pop("passed") is True, arm
        assert set(audit) == expected
        assert all(row["finite"] and row["live"] for row in audit.values())


def test_g35_process_source_is_bounded_paired_and_seed_isolated() -> None:
    formal = g35.make_process_ledgers(
        replicate=0, capacity=8, episode_count=8, formal=True
    )
    nonformal = g35.make_process_ledgers(
        replicate=0, capacity=8, episode_count=8, formal=False
    )
    assert len({row.signature for row in formal}) == 8
    assert [row.signature for row in formal] != [row.signature for row in nonformal]
    for row in formal:
        assert row.event_times in g35.g34.TIME_TUPLES
        assert row.event_order in g35.g34.EVENT_ORDERS
        assert min(row.expected_roster_sizes) > 0
        assert max(row.expected_roster_sizes) <= row.member_capacity
        assert row.base.episode_id == row.episode_id
    formal_seeds = g35.seed_block(2, formal=True)
    nonformal_seeds = g35.seed_block(2, formal=False)
    assert all(
        nonformal_seeds[name] - formal_seeds[name] == g35.NONFORMAL_SEED_OFFSET
        for name in formal_seeds
    )
    assert (
        g35.bootstrap_seed(formal=False) - g35.bootstrap_seed(formal=True)
        == g35.NONFORMAL_SEED_OFFSET
    )


def test_current_state_witness_exceeds_registered_floor() -> None:
    values = [
        g35.current_state_witness_utility(load, mix)
        for load in np.linspace(0.30, 0.70, 101)
        for mix in np.linspace(0.25, 0.75, 101)
    ]
    assert min(values) >= g35.CURRENT_STATE_WITNESS_FLOOR


@pytest.mark.parametrize("bad", ("", "rec", "OTHER"))
def test_unknown_carry_mode_fails_closed(bad: str) -> None:
    with pytest.raises(ValueError, match="REC or CS"):
        g35.make_model(8, carry_mode=bad, initialization_seed=1)
