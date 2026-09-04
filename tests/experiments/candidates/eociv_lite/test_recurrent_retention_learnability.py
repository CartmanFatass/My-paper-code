from __future__ import annotations

import json

import numpy as np
import pytest
import torch

torch.set_num_threads(1)

from experiments.candidates.eociv_lite import actuation_runtime as art
from experiments.candidates.eociv_lite import payload_content_learnability as b2
from experiments.candidates.eociv_lite import real_valve_learning as b1
from experiments.candidates.eociv_lite import recurrent_retention_learnability as b4
from experiments.candidates.eociv_lite import sibling_env as sib


def _actor(seed: int = 71) -> b1.RecurrentActorCritic:
    return b1.RecurrentActorCritic(
        b4.PROFILES[0].member_capacity, seed, encoder_kind="content_separating"
    )


def _slot_block(capacity: int, row: int, body: bytes) -> np.ndarray:
    block = np.zeros((capacity, art.SLOT_DIM), dtype=np.float32)
    block[row] = art.slot_features(sib._pad_slot(body))
    return block


def test_registered_plans_counts_and_nonoverlapping_matched_ids_are_exact() -> None:
    assert b4.FULL_PLAN.training_episodes == 576
    assert b4.FULL_PLAN.training_updates_per_actor == 96
    assert b4.FULL_PLAN.training_transitions == 27_648
    assert b4.FULL_PLAN.evaluation_episodes == 648
    assert b4.FULL_PLAN.evaluation_transitions == 31_104
    assert b4.FULL_PLAN.maximum_transitions == 58_752
    assert b4.SMOKE_PLAN.training_episodes == 12
    assert b4.SMOKE_PLAN.training_updates_per_actor == 6
    assert b4.SMOKE_PLAN.mid_update == 3
    assert b4.SMOKE_PLAN.evaluation_episodes == 54
    assert b4.SMOKE_PLAN.maximum_transitions == 3_168

    identities = {
        stage: b4.episode_id(stage, 2, 1, 3)
        for stage in ("train", *b4.CHECKPOINTS)
    }
    assert identities == {
        "train": 10_210_003,
        "INIT": 11_210_003,
        "MID": 12_210_003,
        "FINAL": 13_210_003,
    }
    assert not set(identities.values()) & {
        6_210_003,
        7_210_003,
        8_210_003,
        9_210_003,
    }
    with pytest.raises(ValueError, match="unregistered B4"):
        b4.episode_id("unknown", 0, 0, 0)


def test_parameter_free_latch_starts_and_ends_zero_without_actor_delta() -> None:
    ephemeral_actor = _actor(72)
    latched_actor = _actor(72)
    ephemeral = b4.RetentionPolicy(ephemeral_actor, "EPHEMERAL_RNN")
    latched = b4.RetentionPolicy(latched_actor, "SEGMENT_LATCH_RNN")
    assert list(ephemeral_actor.state_dict()) == list(latched_actor.state_dict())
    assert all(
        torch.equal(left, right)
        for left, right in zip(ephemeral_actor.state_dict().values(), latched_actor.state_dict().values())
    )
    assert sum(parameter.numel() for parameter in ephemeral_actor.parameters()) == sum(
        parameter.numel() for parameter in latched_actor.parameters()
    )
    assert not isinstance(latched, torch.nn.Module)
    assert not hasattr(latched, "parameters")
    latched.initial_state()
    assert latched.started_zero and not np.any(latched.latch)
    latched.latch[0, 0] = np.float32(1.0)
    latched.end_episode()
    assert latched.ended_zero and not np.any(latched.latch)


def test_latch_retains_replaces_whole_block_and_never_reactivates_stale_row() -> None:
    policy = b4.RetentionPolicy(_actor(73), "SEGMENT_LATCH_RNN")
    hidden = policy.initial_state()
    capacity = policy.capacity
    observations = np.zeros((capacity, b1.roster_env.OBSERVATION_DIM), dtype=np.float32)
    noise = np.zeros((capacity, b1.roster_env.ACTION_DIM), dtype=np.float32)
    active = np.ones(capacity, dtype=np.bool_)
    signal_a = _slot_block(capacity, 0, sib.real_payload_body(sib.SHOCK_A))
    neutral = _slot_block(capacity, 1, sib.NEUTRAL_TOKEN)
    zero = np.zeros_like(signal_a)

    policy.accept_verified_slot(signal_a, active)
    _, _, hidden = policy.forward(observations, active, signal_a, hidden, noise)
    _, _, hidden = policy.forward(observations, active, zero, hidden, noise)
    assert np.array_equal(policy.steps[-1]["effective_slot_block"], signal_a)

    policy.accept_verified_slot(neutral, active)
    _, _, hidden = policy.forward(observations, active, neutral, hidden, noise)
    assert np.array_equal(policy.steps[-1]["effective_slot_block"], neutral)
    assert not np.any(policy.steps[-1]["effective_slot_block"][0])

    inactive = active.copy()
    inactive[1] = False
    _, _, hidden = policy.forward(observations, inactive, zero, hidden, noise)
    assert not np.any(policy.latch[1])
    _, _, _ = policy.forward(observations, active, zero, hidden, noise)
    assert not np.any(policy.steps[-1]["effective_slot_block"][1])


def test_actual_runner_validates_before_accepting_exact_boundaries_and_latches_neutral() -> None:
    actor = _actor(74)
    profile = b4.PROFILES[0]
    env = b1._make_env(profile, b4.episode_id("INIT", 0, 0, 0))
    policy = b4.RetentionPolicy(actor, "SEGMENT_LATCH_RNN")
    runner = b4.RetentionEpisodeRunner(
        env,
        "LR",
        tape_seed=b1.TAPE_SEED,
        d_learned_fn=lambda _: True,
        body_fn=b2._native_neutral_body,
        policy=policy,
    )
    order: list[tuple[str, int]] = []
    original_verify = runner._verify_pre_receipt
    original_accept = policy.accept_verified_slot

    def verify(*args, **kwargs):
        original_verify(*args, **kwargs)
        order.append(("verified", int(env.time)))

    def accept(*args, **kwargs):
        order.append(("accepted", int(env.time)))
        original_accept(*args, **kwargs)

    runner._verify_pre_receipt = verify
    policy.accept_verified_slot = accept
    runner.run_episode()

    assert runner.accepted_boundary_ticks == [12, 24, 36]
    assert order == [
        ("verified", 12),
        ("accepted", 12),
        ("verified", 24),
        ("accepted", 24),
        ("verified", 36),
        ("accepted", 36),
    ]
    assert [record.actuation_route for record in runner.boundary_records] == ["REAL"] * 3
    assert [record.receipt.ingestion_cost for record in runner.boundary_records] == [1] * 3
    for event_time in sib.EVENT_TIMES:
        event_index = sib.EVENT_TIMES.index(event_time)
        focal = runner.boundary_records[event_index].receipt.opportunity_identity.receiver_member_key
        boundary = policy.steps[event_time]
        after = policy.steps[event_time + 1]
        assert b4._slot_label(boundary["effective_slot_block"][focal]) == "NATIVE_NEUTRAL"
        assert np.any(boundary["effective_slot_block"][focal])
        assert b4._slot_label(after["effective_slot_block"][focal]) in {
            "NATIVE_NEUTRAL",
            "ZERO",
        }
        assert not np.any(after["external_slot_block"])
    assert policy.ended_zero and not np.any(policy.latch)


def test_ephemeral_runner_keeps_nonboundary_effective_input_zero() -> None:
    runner = b4._make_runner(
        _actor(75),
        "EPHEMERAL_RNN",
        b4.PROFILES[0],
        b4.episode_id("INIT", 0, 0, 1),
        b2._correct_body,
    )
    assert runner.accepted_boundary_ticks == [12, 24, 36]
    for time, step in enumerate(runner.policy.steps):
        if time not in sib.EVENT_TIMES:
            assert not np.any(step["external_slot_block"])
            assert not np.any(step["effective_slot_block"])


def test_lag_schema_and_early_late_mass_math_are_exact() -> None:
    rows = []
    for checkpoint in b4.CHECKPOINTS:
        for event_time in b4.CRITICAL_EVENT_TIMES:
            for contrast in b4.CONTRASTS:
                for lag in range(sib.SEGMENT_LENGTH):
                    absolute = 2.0 if lag < 4 else 1.0
                    rows.append(
                        {
                            "condition": "EPHEMERAL_RNN",
                            "checkpoint": checkpoint,
                            "actor_seed": 86031,
                            "profile": b4.PROFILES[0].name,
                            "root": 0,
                            "event_time": event_time,
                            "contrast": contrast,
                            "lag": lag,
                            "internal_slot_l1": 0.0,
                            "recurrent_state_l1": 0.0,
                            "kernel_l1": 0.0,
                            "sampled_action_l1": 0.0,
                            "signed_reward_difference": -absolute,
                            "absolute_reward_difference": absolute,
                        }
                    )
    plan = b4.ExperimentPlan(
        "proof",
        ("EPHEMERAL_RNN",),
        (86031,),
        (b4.PROFILES[0],),
        1,
        1,
        1,
    )
    summaries = b4._lag_summaries(rows, plan)
    assert len(summaries) == 12
    sample = summaries[0]
    assert len(sample["lags"]) == 12
    assert sample["early_reward_absolute_mass"] == pytest.approx(8.0)
    assert sample["late_reward_absolute_mass"] == pytest.approx(8.0)
    assert sample["early_reward_absolute_mass_share"] == pytest.approx(0.5)
    assert sample["late_reward_absolute_mass_share"] == pytest.approx(0.5)
    assert set(sample["lags"][0]) == {
        "lag",
        "internal_slot_l1",
        "recurrent_state_l1",
        "kernel_l1",
        "sampled_action_l1",
        "signed_reward_difference",
        "absolute_reward_difference",
    }


def test_registered_smoke_is_real_matched_complete_and_canonical() -> None:
    first = b4.run_experiment("smoke")
    second = b4.run_experiment("smoke")
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["mechanical_status"] == "MECHANICAL_B4_COMPLETE"
    assert first["scientific_disposition"] is None
    assert first["registered_c_outcome_experiment_licensed"] is False
    assert first["counts"] == {
        "environment_transitions": 3_168,
        "policy_calls": 3_168,
        "actor_critic_optimizer_steps": 12,
        "training_episodes": 12,
        "evaluation_episodes": 54,
    }
    assert all(first["matching_proof"].values())
    assert len(first["actors"]) == 2
    assert len(first["evaluation_rows"]) == 18
    assert len(first["contrast_root_rows"]) == 18 * 2 * 2 * 12
    assert len(first["lag_summaries"]) == 2 * 3 * 1 * 3 * 2 * 2
    assert len(first["paired_condition_final_minus_init"]) == 3
    for row in first["evaluation_rows"]:
        assert set(row["arms"]) == set(b4.EVALUATION_ARMS)
        for arm in row["arms"].values():
            assert len(arm["lag_evidence"]) == 24
            assert arm["accepted_boundary_ticks"] == [12, 24, 36]
            assert arm["latch_started_zero"] and arm["latch_ended_zero"]
