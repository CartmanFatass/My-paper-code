from __future__ import annotations

import inspect

import numpy as np
import pytest
import torch

from envs.continuous_roster import runtime_capacity as roster_env
from experiments.candidates.eociv_lite import actuation_runtime as art
from experiments.candidates.eociv_lite import payload_content_learnability as b2
from experiments.candidates.eociv_lite import real_valve_learning as b1
from experiments.candidates.eociv_lite import sibling_env as sib


def _slot_block(*bodies: bytes) -> np.ndarray:
    rows = np.zeros((len(bodies), art.SLOT_DIM), dtype=np.float32)
    for index, body in enumerate(bodies):
        rows[index] = art.slot_features(sib._pad_slot(body))
    return rows


def test_registered_full_and_smoke_budgets_are_exact() -> None:
    assert b2.FULL_PLAN.training_transitions == 27_648
    assert b2.FULL_PLAN.evaluation_transitions == 20_736
    assert b2.FULL_PLAN.maximum_transitions == 48_384
    assert b2.FULL_PLAN.optimizer_steps == 576
    assert b2.FULL_PLAN.evaluation_episodes == 432
    assert b2.SMOKE_PLAN.maximum_transitions == 1_152
    assert b2.SMOKE_PLAN.optimizer_steps == 6
    assert b2.SMOKE_PLAN.evaluation_episodes == 18


def test_default_raw_encoder_matches_explicit_raw_and_shared_initialization() -> None:
    capacity = b2.PROFILES[0].member_capacity
    default = b1.RecurrentActorCritic(capacity, 86031)
    raw = b1.RecurrentActorCritic(capacity, 86031, encoder_kind="raw_byte")
    content = b1.RecurrentActorCritic(
        capacity, 86031, encoder_kind="content_separating"
    )
    assert default.encoder_kind == "raw_byte"
    for name, value in default.state_dict().items():
        assert torch.equal(value, raw.state_dict()[name])
        assert torch.equal(value, content.state_dict()[name])

    observations = np.zeros((capacity, roster_env.OBSERVATION_DIM), np.float32)
    active = np.ones(capacity, np.bool_)
    slots = np.zeros((capacity, art.SLOT_DIM), np.float32)
    noise = np.zeros((capacity, roster_env.ACTION_DIM), np.float32)
    expected = default.forward(
        observations, active, slots, default.initial_state(), noise
    )
    actual = raw.forward(observations, active, slots, raw.initial_state(), noise)
    for left, right in zip(expected, actual):
        assert np.array_equal(left, right)


def test_content_encoder_recognizes_only_registered_actual_slot_bytes() -> None:
    slots = _slot_block(
        b"",
        sib.real_payload_body(sib.SHOCK_A),
        sib.real_payload_body(sib.SHOCK_B),
        sib.NEUTRAL_TOKEN,
    )
    assert np.array_equal(
        b1.RecurrentActorCritic._content_indices(slots),
        np.asarray((0, 1, 2, 3), dtype=np.int64),
    )
    with pytest.raises(ValueError, match="unknown nonzero"):
        b1.RecurrentActorCritic._content_indices(_slot_block(b"EOCIV-UNKNOWN"))
    malformed = slots.copy()
    malformed[0, 0] = np.float32(0.123)
    with pytest.raises(ValueError, match="exact receiver slot bytes"):
        b1.RecurrentActorCritic._content_indices(malformed)


def test_diagnostic_step_is_pure_and_does_not_change_capture_state() -> None:
    capacity = b2.PROFILES[0].member_capacity
    actor = b1.RecurrentActorCritic(
        capacity, 86031, encoder_kind="content_separating"
    )
    observations = np.zeros((capacity, roster_env.OBSERVATION_DIM), np.float32)
    active = np.ones(capacity, np.bool_)
    slots = np.zeros((capacity, art.SLOT_DIM), np.float32)
    noise = np.zeros((capacity, roster_env.ACTION_DIM), np.float32)
    hidden = actor.initial_state()
    first = actor.diagnostic_step(observations, active, slots, hidden, noise)
    second = actor.diagnostic_step(observations, active, slots, hidden, noise)
    assert actor._graph_hidden is None
    assert actor._log_probs == []
    assert actor._values == []
    for left, right in zip(first, second):
        assert np.array_equal(left, right)


def test_body_selector_seam_is_default_safe_and_mutually_exclusive() -> None:
    profile = b2.PROFILES[0]
    registered_id = b2.episode_id("evaluation", 0, 0, 0)
    default_env = b1._make_env(profile, registered_id)
    explicit_env = b1._make_env(profile, registered_id)
    default = art.ArmEpisodeRunner(
        default_env,
        "LR",
        tape_seed=b1.TAPE_SEED,
        d_learned_fn=lambda _: True,
    )
    explicit = art.ArmEpisodeRunner(
        explicit_env,
        "LR",
        tape_seed=b1.TAPE_SEED,
        d_learned_fn=lambda _: True,
        body_fn=lambda event, env: env.focal_payload(event),
    )
    default.run_episode()
    explicit.run_episode()
    assert default.step_traces == explicit.step_traces
    assert default.boundary_records == explicit.boundary_records
    with pytest.raises(ValueError, match="mutually exclusive"):
        art.ArmEpisodeRunner(
            b1._make_env(profile, registered_id),
            "LR",
            tape_seed=b1.TAPE_SEED,
            d_learned_fn=lambda _: True,
            body_override=sib.NEUTRAL_TOKEN,
            body_fn=b2._correct_body,
        )


def test_body_rules_change_only_registered_payload_content() -> None:
    env = b1._make_env(b2.PROFILES[0], b2.episode_id("evaluation", 0, 0, 1))
    for event_index, cell_class in enumerate(sib.CELL_CLASS):
        correct = b2._correct_body(event_index, env)
        swapped = b2._swapped_body(event_index, env)
        neutral = b2._native_neutral_body(event_index, env)
        assert neutral == sib.NEUTRAL_TOKEN
        if cell_class == "NEUTRAL":
            assert correct == swapped == neutral
        else:
            assert correct == env.focal_payload(event_index)
            assert swapped != correct
            assert {correct, swapped} == {
                sib.real_payload_body(sib.SHOCK_A),
                sib.real_payload_body(sib.SHOCK_B),
            }
            expected = {
                sib.real_payload_body(sib.SHOCK_A): sib.real_payload_body(
                    sib.SHOCK_B
                ),
                sib.real_payload_body(sib.SHOCK_B): sib.real_payload_body(
                    sib.SHOCK_A
                ),
            }
            assert swapped == expected[env.focal_payload(event_index)]


def test_b2_source_does_not_read_private_shock_state_storage() -> None:
    assert "_shock_states" not in inspect.getsource(b2)


def test_real_smoke_runs_both_encoders_learner_and_three_arm_evaluator() -> None:
    result = b2.run_experiment("smoke")
    assert result["mechanical_status"] == "MECHANICAL_B2_COMPLETE"
    assert result["scientific_disposition"] is None
    assert result["registered_c_outcome_experiment_licensed"] is False
    assert result["real_environment_calls"] is True
    assert result["real_policy_calls"] is True
    assert result["real_actor_learner_updates"] is True
    assert result["real_evaluation_runner_calls"] is True
    assert result["counts"] == {
        "environment_transitions": 1_152,
        "policy_calls": 1_152,
        "actor_critic_optimizer_steps": 6,
        "training_episodes": 6,
        "evaluation_episodes": 18,
    }
    assert {row["encoder_kind"] for row in result["actors"]} == set(
        b2.ENCODER_KINDS
    )
    for actor_row in result["actors"]:
        assert actor_row["training_profile_order"] == [
            profile.name for profile in b2.PROFILES
        ]
        assert actor_row["instability_diagnostics"]["all_finite"] is True
    assert len(result["evaluation_rows"]) == 6
    for row in result["evaluation_rows"]:
        assert set(row["arms"]) == set(b2.EVALUATION_ARMS)
        assert len(row["delivered_registered_body_labels"]) == len(sib.EVENT_TIMES)
        assert set(row["delivered_registered_body_labels"]) <= {
            "SIGNAL_A",
            "SIGNAL_B",
            "NATIVE_NEUTRAL",
        }
        assert len(row["initial_ab_diagnostics"]) == len(sib.EVENT_TIMES)
        assert len(row["trained_ab_diagnostics"]) == len(sib.EVENT_TIMES)
        for arm in row["arms"].values():
            assert arm["routes"] == ["REAL"] * len(sib.EVENT_TIMES)
            assert len(arm["reward_trace"]) == roster_env.HORIZON
            assert len(arm["kernel_digests"]) == roster_env.HORIZON
            assert len(arm["sampled_action_digests"]) == roster_env.HORIZON
            assert len(arm["recurrent_state_digests"]) == roster_env.HORIZON
        correct = row["arms"]["CORRECT"]["segment_returns"]
        swapped = row["arms"]["SWAPPED"]["segment_returns"]
        neutral = row["arms"]["NATIVE_NEUTRAL"]["segment_returns"]
        assert row["segment_correct_minus_swapped"] == [
            left - right for left, right in zip(correct, swapped)
        ]
        assert row["segment_correct_minus_native_neutral"] == [
            left - right for left, right in zip(correct, neutral)
        ]
    for summary in result["encoder_summaries"].values():
        for key in (
            "segment_correct_minus_swapped",
            "segment_correct_minus_native_neutral",
        ):
            assert len(summary[key]) == roster_env.HORIZON // sib.SEGMENT_LENGTH
            assert [row["segment_index"] for row in summary[key]] == [0, 1, 2, 3]
            assert all(row["count"] == 3 for row in summary[key])
