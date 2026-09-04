"""Focused contracts for the EOCIV-B1 real valve-learning package."""

from __future__ import annotations

import inspect
from dataclasses import asdict

import numpy as np
import pytest
import torch

from envs.continuous_roster import runtime_capacity as roster_env
from experiments.candidates.eociv_lite import actuation_runtime as art
from experiments.candidates.eociv_lite import capability_gate
from experiments.candidates.eociv_lite import real_valve_learning as b1
from experiments.candidates.eociv_lite import sibling_env as sib


PROFILE = roster_env.TRAIN_PROFILES[0]


def _record(**overrides) -> b1.ValveFeatureRecord:
    values = dict(
        sender_role="CAPABILITY_0",
        receiver_role="CAPABILITY_1",
        active_member_count=4.0,
        incoming_hard_valid_edge_count=3.0,
        sender_spell_age_bin="5_TO_16",
        receiver_spell_age_bin="0_TO_4",
        payload_age=0.0,
        policy_version_distance=0.0,
    )
    values.update(overrides)
    return b1.ValveFeatureRecord(**values)


def test_default_runner_is_identical_to_explicit_common_policy():
    default = art.ArmEpisodeRunner(
        capability_gate._make_sibling(PROFILE, 5),
        "LR",
        tape_seed=capability_gate.TAPE_SEED,
        d_learned_fn=capability_gate.registered_learned_decision,
    )
    explicit = art.ArmEpisodeRunner(
        capability_gate._make_sibling(PROFILE, 5),
        "LR",
        tape_seed=capability_gate.TAPE_SEED,
        d_learned_fn=capability_gate.registered_learned_decision,
        policy=art.CommonPolicy(PROFILE.member_capacity),
    )
    assert default.run_episode() == explicit.run_episode()
    assert default.step_traces == explicit.step_traces
    assert default.boundary_records == explicit.boundary_records


def test_default_cs_still_executes_registered_stage0_control_tape():
    episode = 6
    runner = art.ArmEpisodeRunner(
        capability_gate._make_sibling(PROFILE, episode),
        "CS",
        tape_seed=capability_gate.TAPE_SEED,
        d_learned_fn=capability_gate.registered_learned_decision,
    )
    runner.run_episode()
    expected = [
        "REAL"
        if sib.control_tape_open(
            PROFILE.name,
            episode,
            event,
            tape_seed=capability_gate.TAPE_SEED,
        )
        else "NEUTRAL"
        for event in range(3)
    ]
    assert [row.actuation_route for row in runner.boundary_records] == expected


def test_injected_cs_control_vector_is_the_executed_route_vector():
    actor = b1.RecurrentActorCritic(PROFILE.member_capacity, 86031)
    registered_id = b1.episode_id("evaluation", 0, 0, 1)
    runner, _ = b1._run_episode(
        PROFILE, registered_id, actor, "CS", [True, False, True]
    )
    assert [row.actuation_route for row in runner.boundary_records] == [
        "REAL",
        "NEUTRAL",
        "REAL",
    ]


def test_recurrent_actor_emits_zero_inactive_actions_and_preserves_hidden():
    actor = b1.RecurrentActorCritic(PROFILE.member_capacity, 86031)
    hidden = actor.initial_state()
    hidden[6:] = 0.75
    observations = np.zeros((PROFILE.member_capacity, roster_env.OBSERVATION_DIM), np.float32)
    active = np.asarray([True] * 6 + [False] * 2)
    slots = np.zeros((PROFILE.member_capacity, art.SLOT_DIM), np.float32)
    noise = np.zeros((PROFILE.member_capacity, roster_env.ACTION_DIM), np.float32)
    actions, kernels, new_hidden = actor.forward(observations, active, slots, hidden, noise)
    assert actions.shape == kernels.shape == (PROFILE.member_capacity, roster_env.ACTION_DIM)
    assert np.isfinite(actions).all() and np.isfinite(new_hidden).all()
    assert np.count_nonzero(actions[~active]) == 0
    assert np.array_equal(new_hidden[~active], hidden[~active])


def test_actor_objective_accepts_only_external_reward_sequence():
    parameters = tuple(inspect.signature(b1.RecurrentActorCritic.episode_loss).parameters)
    assert parameters == ("self", "rewards")
    assert not (b1.FORBIDDEN_VALVE_FIELDS & b1.FEATURE_KEYS)


def test_valve_feature_contract_is_exact_and_fail_closed():
    material = asdict(_record())
    vector = b1.encode_valve_features(material)
    assert vector.shape == (b1.FEATURE_DIM,) and np.isfinite(vector).all()
    with pytest.raises(b1.ValveInputError):
        b1.encode_valve_features({**material, "shock": "A"})
    missing = dict(material)
    missing.pop("payload_age")
    with pytest.raises(b1.ValveInputError):
        b1.encode_valve_features(missing)
    with pytest.raises(b1.ValveInputError):
        b1.encode_valve_features({**material, "sender_role": "UNSEEN"})
    with pytest.raises(b1.ValveInputError):
        b1.encode_valve_features({**material, "active_member_count": float("nan")})


def test_detached_valve_updates_without_actor_gradient_path():
    actor = b1.RecurrentActorCritic(PROFILE.member_capacity, 86031)
    valve = b1.DetachedRidgeValve(86031)
    records = [_record(sender_role="CAPABILITY_0"), _record(sender_role="CAPABILITY_1")]
    valve.fit(records, [0, 1])
    assert valve.fitted and valve.optimizer_steps == b1.VALVE_STEPS
    assert all(parameter.grad is None for parameter in actor.parameters())
    assert any(parameter.grad is not None for parameter in valve.parameters())


def test_one_sided_support_hard_opens_without_optimizer_step():
    valve = b1.DetachedRidgeValve(86031)
    valve.fit([_record(), _record(receiver_role="CAPABILITY_0")], [1, 1])
    decision, score, status = valve.decide(_record())
    assert decision is True and score is None and status == "SUPPORT_MISSING"
    assert valve.optimizer_steps == 0


def test_paired_receipt_clones_share_root_and_change_only_focal_route():
    actor = b1.RecurrentActorCritic(PROFILE.member_capacity, 86031)
    plan = b1.ExperimentPlan("unit", (86031,), (PROFILE,), 1, 1, 1, 1)
    counts = {
        "environment_transitions": 0,
        "policy_calls": 0,
        "actor_critic_optimizer_steps": 0,
        "valve_optimizer_steps": 0,
        "training_episodes": 0,
        "receipt_clone_episodes": 0,
        "evaluation_episodes": 0,
        "valve_fallback_events": 0,
    }
    records, labels, calibration, raw = b1._build_receipts(actor, 0, plan, counts)
    assert len(records) == len(labels) == 3 and not calibration[PROFILE.name]
    assert all(row["shared_root_material"] for row in raw)
    assert all(row["real_route"] == "REAL" and row["neutral_route"] == "NEUTRAL" for row in raw)
    assert counts["environment_transitions"] == 6 * roster_env.HORIZON


def test_lr_cr_identity_and_control_schedule_are_exact_and_content_blind():
    actor = b1.RecurrentActorCritic(PROFILE.member_capacity, 86031)
    registered_id = b1.episode_id("evaluation", 0, 0, 0)
    lr, _ = b1._run_episode(PROFILE, registered_id, actor, "LR", [True] * 3)
    cr, _ = b1._run_episode(PROFILE, registered_id, actor, "CR", [True] * 3)
    assert lr.step_traces == cr.step_traces
    first, target = b1._control_schedule(86031, PROFILE.name, 16, 4, 9)
    second, target_again = b1._control_schedule(86031, PROFILE.name, 16, 4, 9)
    assert first == second and target == target_again
    assert sum(not value for value in first.values()) == target
    assert set(first) == {(root, event) for root in range(16) for event in range(3)}


def test_budget_and_episode_namespaces_are_frozen_and_disjoint():
    assert b1.FULL_PLAN.maximum_transitions == 72_576
    ids = {
        b1.episode_id(stage, actor, profile, root)
        for stage in ("train", "receipt", "evaluation")
        for actor in range(3)
        for profile in range(3)
        for root in range(16)
    }
    assert len(ids) == 3 * 3 * 3 * 16
    assert capability_gate.REGISTERED_OUTCOME_EXPERIMENT["licensed"] is False


def test_real_smoke_invokes_environment_both_learners_and_evaluator():
    result = b1.run_experiment("smoke")
    counts = result["counts"]
    assert result["real_environment_calls"] and result["real_policy_calls"]
    assert result["real_actor_learner_updates"] and result["real_valve_learner_updates"]
    assert result["real_evaluation_runner_calls"]
    assert counts["environment_transitions"] == b1.SMOKE_PLAN.maximum_transitions
    assert counts["policy_calls"] == counts["environment_transitions"]
    assert counts["actor_critic_optimizer_steps"] > 0
    assert counts["valve_optimizer_steps"] == b1.VALVE_STEPS
    assert counts["evaluation_episodes"] > 0
    assert all(row["lr_cr_identical"] for row in result["evaluation_rows"])
    assert result["registered_c_outcome_experiment_licensed"] is False
