from __future__ import annotations

from dataclasses import replace
import copy
import json
import random
import subprocess
import sys
import types

import numpy as np
import pytest
import torch

from experiments.candidates.complementary_skill_learning.b01 import runner as b01
from experiments.candidates.complementary_skill_learning.b02.runner import effective_config
from experiments.candidates.complementary_skill_learning.b04 import runner as r
from experiments.candidates.complementary_skill_learning.b04.learning import (
    PersistentProcessRNG,
    UNIFORM_LOG_FACTOR,
)


@pytest.fixture(scope="module")
def spec():
    return replace(
        r.DEFAULT_SPEC,
        n_users=8,
        horizon=20,
        lanes=2,
        rollouts=1,
        eval_lanes=2,
        threads=1,
        small_model=True,
    )


def build(tmp_path, spec, arm, suffix=""):
    envs = r.make_envs(spec, spec.lanes, spec.train_world_base)
    config = r.make_config(spec, envs, arm)
    r.seed_rng(spec.init_seed)
    agent = r.TrainingLawAgent(
        config=config,
        arm=arm,
        head_seed=spec.head_seed,
        aux_seed=spec.aux_seed,
        low_action_seed=spec.low_action_seed,
        high_collection_seed=spec.high_collection_seed,
        high_update_seed=spec.high_update_seed,
        log_dir=str(tmp_path / f"logs-{arm}{suffix}"),
        device=torch.device("cpu"),
    )
    return agent, envs


def collect_rollout(agent, envs, spec):
    telemetry = r._storage_telemetry()
    states, observations = b01.native._reset_all(envs)
    env_steps = np.zeros(spec.lanes, np.int64)
    dones = np.zeros(spec.lanes, bool)
    for t in range(spec.horizon):
        actions, _, data = agent.step(
            states,
            observations,
            env_steps,
            dones,
            deterministic=False,
            return_step_data=True,
            build_infos=False,
        )
        next_states, next_obs, rewards, next_dones = [], [], [], []
        for lane, env in enumerate(envs):
            state, obs, reward, done, _, _ = r.physical_step(env, actions[lane])
            next_states.append(state)
            next_obs.append(obs)
            rewards.append(reward)
            next_dones.append(done)
        next_states = np.stack(next_states)
        next_obs = np.stack(next_obs)
        next_dones = np.asarray(next_dones)
        r.store_verified_batch(
            agent,
            telemetry,
            states=states,
            next_states=next_states.copy(),
            observations=observations,
            next_observations=next_obs.copy(),
            actions=actions,
            rewards=np.asarray(rewards),
            dones=next_dones,
            infos_batch=None,
            rollout_step_idx=t,
            step_data=data,
        )
        states, observations, dones = next_states, next_obs, next_dones
        env_steps += 1
    return states, observations, dones, telemetry


@pytest.fixture(scope="module")
def pair(tmp_path_factory, spec):
    root = tmp_path_factory.mktemp("b04-pair")
    summaries = {
        arm: r.run_fit(arm, root / arm, "technical-check", spec=spec, device="cpu")
        for arm in ("M", "U")
    }
    return root, summaries


def test_fixed_protocol_addresses_and_effective_switches(spec):
    fixed = r.DEFAULT_SPEC
    assert (
        fixed.init_seed,
        fixed.head_seed,
        fixed.train_rng_seed,
        fixed.aux_seed,
        fixed.low_action_seed,
        fixed.high_collection_seed,
        fixed.high_update_seed,
    ) == (
        260923931,
        260923932,
        260923933,
        260923934,
        260923935,
        260923936,
        260923937,
    )
    assert fixed.train_world_base == 2100000
    assert fixed.eval_rng_seed == 260923905
    assert fixed.eval_world_base == 1700200
    assert fixed.lanes * fixed.horizon * fixed.rollouts == 360000
    assert 6 * fixed.eval_lanes * fixed.horizon == 96000
    assert r._uniform_stream_digest(fixed) == r.EXPECTED_UNIFORM_LABEL_STREAM_SHA256

    for arm in ("M", "U"):
        envs = r.make_envs(spec, spec.lanes, spec.train_world_base)
        try:
            config = r.make_config(spec, envs, arm)
            snapshot = effective_config(config)
        finally:
            for env in envs:
                env.close()
        assert config.disable_high_level_training == (arm == "U")
        assert snapshot["legacy_mi_reward_coef"] == 0.5
        assert snapshot["effective_team_discriminator_reward_coef"] == 0.025
        assert snapshot["effective_individual_discriminator_reward_coef"] == 0.01
        assert config.policy_interruption_mode == "d2"
        assert config.interruption_cost_c == float("inf")
        assert config.interruption_cost_c_Z == float("inf")
        assert config.skill_cap_k_max == config.team_cap_k_Z == 10
        assert not config.use_obsnorm and not config.use_statenorm


def test_actual_initial_tensors_and_external_uniform_panels_match(pair):
    root, summaries = pair
    learned, uniform = summaries["M"], summaries["U"]
    assert learned["initial_native_digest"] == uniform["initial_native_digest"]
    assert learned["initial_frozen_digest"] == uniform["initial_frozen_digest"]
    assert learned["initial_default_rng_state_sha256"] == uniform[
        "initial_default_rng_state_sha256"
    ]
    assert learned["initial_private_rng_streams"] == uniform["initial_private_rng_streams"]

    m_checkpoint = torch.load(
        root / "M" / "initial.pt", map_location="cpu", weights_only=False
    )
    u_checkpoint = torch.load(
        root / "U" / "initial.pt", map_location="cpu", weights_only=False
    )
    for module, state in m_checkpoint["native"].items():
        for name, value in state.items():
            assert torch.equal(value, u_checkpoint["native"][module][name])
    for head in ("g_head", "p_head"):
        for name, value in m_checkpoint["auxiliary"][head].items():
            assert torch.equal(value, u_checkpoint["auxiliary"][head][name])
    assert set(m_checkpoint["rng"]["private_streams"]) == {
        "low_actions",
        "high_collection",
        "high_updates",
    }
    assert set(m_checkpoint["rng"]["rollout_samplers"]) == {
        "remaining_learner",
        "high_updates",
    }

    m_panel = learned["panels"]["initial_uniform"]
    u_panel = uniform["panels"]["initial_uniform"]
    for name in (
        "returns_U",
        "native_scores_J",
        "component_means",
        "connected_users_per_step",
        "physical_initial_state_sha256",
        "selected_label_stream_sha256",
    ):
        assert r.jsonable(m_panel[name]) == r.jsonable(u_panel[name])


def test_real_pair_counts_movements_panels_and_rng_isolation(pair):
    _, summaries = pair
    learned, uniform = summaries["M"], summaries["U"]
    for arm, summary in summaries.items():
        assert summary["status"] == "complete"
        panel_count = 4 if arm == "M" else 2
        assert summary["counts"] == {
            "started_fits": 1,
            "model_constructions": 1,
            "training_transitions": 40,
            "stored_transitions": 40,
            "training_episodes": 2,
            "native_updates": 1,
            "evaluation_transitions": panel_count * 40,
            "evaluation_episodes": panel_count * 2,
        }
        assert summary["label_flow_checks"] == {
            "action_batches": 20,
            "reward_batches": 20,
            "factual_batches": 20,
            "storage_batches": 20,
            "failures": 0,
        }
        movement = summary["training_rows"][0]["relative_initialization_displacement"]
        assert all(
            movement[name] > 0
            for name in (
                "discoverer_actor",
                "discoverer_critic",
                "team_discriminator",
                "individual_discriminator",
            )
        )
        assert all(
            summary["training_rows"][0]["auxiliary_head_relative_movement"][name] > 0
            for name in ("G", "P")
        )
        assert summary["training_rows"][0]["auxiliary"]["trunk_optimizer_steps"] == 0
        assert all(
            value == 0
            for value in summary["training_rows"][0]["auxiliary"][
                "trunk_relative_movement"
            ].values()
        )
        retained = summary["d2_retained_work"][0]
        assert retained["decision_rows"] == 4
        assert retained["team_valid_rows"] == 4
        assert retained["agent_valid_rows"] == 24
        assert retained["metrics"]["coordinator_inference_calls"] > 0
        assert retained["metrics"]["team_decisions"] == 4
        assert retained["metrics"]["sampled_total"] == 24

    assert learned["training_rows"][0]["relative_initialization_displacement"][
        "coordinator"
    ] > 0
    assert uniform["training_rows"][0]["relative_initialization_displacement"][
        "coordinator"
    ] == 0
    assert learned["native_optimizer_calls"]["coordinator"] > 0
    assert uniform["native_optimizer_calls"]["coordinator"] == 0
    assert uniform["d2_retained_work"][0]["metrics"]["optimizer_steps"] == 0

    # Both arms consumed exactly the same low-action and high-collection draws.
    # The native coordinator currently uses its object-private sampler and no
    # process-global draw, so the isolated high-update process stream stays at
    # its initial address in both arms; U's skip cannot move the low stream.
    assert learned["final_private_rng_streams"]["low_actions"] == uniform[
        "final_private_rng_streams"
    ]["low_actions"]
    assert learned["final_private_rng_streams"]["high_collection"] == uniform[
        "final_private_rng_streams"
    ]["high_collection"]
    assert uniform["final_private_rng_streams"]["high_updates"] == uniform[
        "initial_private_rng_streams"
    ]["high_updates"]
    assert learned["final_private_rng_streams"]["high_updates"] == learned[
        "initial_private_rng_streams"
    ]["high_updates"]
    assert learned["training_rows"][0]["default_rng_state_sha256_after"] == uniform[
        "training_rows"
    ][0]["default_rng_state_sha256_after"]
    assert learned["final_sampler_rng_streams"]["remaining_learner"] == uniform[
        "final_sampler_rng_streams"
    ]["remaining_learner"]
    assert uniform["final_sampler_rng_streams"]["high_updates"] == uniform[
        "initial_sampler_rng_streams"
    ]["high_updates"]
    assert learned["final_sampler_rng_streams"]["high_updates"] != learned[
        "initial_sampler_rng_streams"
    ]["high_updates"]


def test_u_records_uniform_factors_without_learned_replay_claim(pair):
    _, summaries = pair
    audits = summaries["U"]["uniform_factor_audits"]
    assert len(audits) == 2  # before native update and after final D2 flush
    for audit in audits:
        assert audit["law"] == "independent_uniform_team_and_individual_1_over_6"
        assert audit["learned_policy_ppo_replay"] == "not_applicable"
        assert audit["expected_log_factor"] == UNIFORM_LOG_FACTOR
        assert audit["canonical_rows_checked"] > 0
        assert audit["team_factors_checked"] > 0
        assert audit["individual_factors_checked"] == 6 * audit["team_factors_checked"]
    assert summaries["M"]["training_rows"][0]["auxiliary"]["native_mu_replay"][
        "law"
    ] == "mu=.9*pi+.1/6"


def test_labels_cannot_change_after_low_forward(tmp_path, spec):
    agent, envs = build(tmp_path, spec, "U")
    try:
        states, observations = b01.native._reset_all(envs)
        actions, _, data = agent.step(
            states,
            observations,
            np.zeros(spec.lanes, np.int64),
            np.zeros(spec.lanes, bool),
            deterministic=False,
            return_step_data=True,
            build_infos=False,
        )
        next_states, next_obs, rewards, dones = [], [], [], []
        for lane, env in enumerate(envs):
            state, obs, reward, done, _, _ = r.physical_step(env, actions[lane])
            next_states.append(state)
            next_obs.append(obs)
            rewards.append(reward)
            dones.append(done)
        data["agent_skills"][0, 0] = (int(data["agent_skills"][0, 0]) + 1) % 6
        with pytest.raises(RuntimeError, match="labels changed"):
            agent.store_transition_batch(
                states=states,
                next_states=np.stack(next_states),
                observations=observations,
                next_observations=np.stack(next_obs),
                actions=actions,
                rewards=np.asarray(rewards),
                dones=np.asarray(dones),
                infos_batch=None,
                rollout_step_idx=0,
                step_data=data,
            )
    finally:
        for env in envs:
            env.close()


def test_u_constant_law_is_state_weight_and_prefix_independent(tmp_path, spec):
    agent, envs = build(tmp_path, spec, "U", suffix="-constant")
    decoder = agent.skill_coordinator.skill_decoder
    batch = 3
    width = int(agent.config.embedding_dim)
    state_a = torch.randn(batch, 1, width)
    obs_a = torch.randn(batch, spec.n_agents, width)
    state_b = torch.randn(batch, 1, width) * 100
    obs_b = torch.randn(batch, spec.n_agents, width) * 100
    team_a = torch.tensor([0, 1, 5])
    team_b = torch.tensor([5, 4, 0])
    prefix_a = torch.tensor([[0, 1], [2, 3], [4, 5]])
    prefix_b = torch.tensor([[5, 4], [3, 2], [1, 0]])
    try:
        before = [
            decoder(state_a, obs_a),
            decoder(
                state_a,
                obs_a,
                team_a,
                prefix_a,
                step=3,
                agent_specific_query=obs_a[:, 2:3],
            ),
            decoder(state_b, obs_b),
            decoder(
                state_b,
                obs_b,
                team_b,
                prefix_b,
                step=3,
                agent_specific_query=obs_b[:, 2:3],
            ),
        ]
        with torch.no_grad():
            for parameter in decoder.parameters():
                parameter.add_(torch.randn_like(parameter) * 10)
        after = [
            decoder(state_a, obs_a),
            decoder(
                state_b,
                obs_b,
                team_b,
                prefix_b,
                step=3,
                agent_specific_query=obs_b[:, 2:3],
            ),
        ]
        assert all(torch.equal(value, torch.zeros_like(value)) for value in before + after)
    finally:
        for env in envs:
            env.close()


def test_extra_high_collection_draws_do_not_shift_low_or_default_rng(tmp_path, spec):
    clean, clean_envs = build(tmp_path, spec, "U", suffix="-clean")
    noisy, noisy_envs = build(tmp_path, spec, "U", suffix="-noisy")
    original = noisy.skill_coordinator.assign_partial_batch

    def with_extra_draws(_self, *args, **kwargs):
        random.random()
        np.random.random()
        torch.rand(7)
        return original(*args, **kwargs)

    noisy.skill_coordinator.assign_partial_batch = types.MethodType(
        with_extra_draws, noisy.skill_coordinator
    )
    try:
        outputs = []
        global_digests = []
        for agent, envs in ((clean, clean_envs), (noisy, noisy_envs)):
            r.seed_rng(spec.train_rng_seed)
            states, observations = b01.native._reset_all(envs)
            before_global = r.rng_state_digest()
            outputs.append(
                agent.step(
                    states,
                    observations,
                    np.zeros(spec.lanes, np.int64),
                    np.zeros(spec.lanes, bool),
                    deterministic=False,
                    return_step_data=True,
                    build_infos=False,
                )
            )
            global_digests.append((before_global, r.rng_state_digest()))
        assert global_digests[0][0] == global_digests[1][0]
        assert global_digests[0][1] == global_digests[1][1]
        assert clean.rng_stream_telemetry()["low_actions"] == noisy.rng_stream_telemetry()[
            "low_actions"
        ]
        assert clean.rng_stream_telemetry()["high_collection"] != noisy.rng_stream_telemetry()[
            "high_collection"
        ]
    finally:
        for env in (*clean_envs, *noisy_envs):
            env.close()


def test_actual_high_update_preserves_low_sampler_and_checkpoint_roundtrip(
    tmp_path, spec
):
    updated, updated_envs = build(tmp_path, spec, "M", suffix="-updated")
    control, control_envs = build(tmp_path, spec, "M", suffix="-control")
    try:
        collect_rollout(updated, updated_envs, spec)
        collect_rollout(control, control_envs, spec)
        for name in (
            "masks",
            "states",
            "obs",
            "actions",
            "rewards",
            "dones",
            "team_skills",
            "agent_skills",
            "d2_team_skill",
            "d2_agent_skills",
            "d2_team_old_log_prob",
            "d2_agent_old_log_probs",
        ):
            np.testing.assert_array_equal(
                getattr(updated.rollout_buffer, name), getattr(control.rollout_buffer, name)
            )

        before = updated.sampler_rng_telemetry()
        control_before = control.sampler_rng_telemetry()
        assert before == control_before
        result = updated.update_coordinator(spec.horizon)
        assert len(result) == 9
        after = updated.sampler_rng_telemetry()
        assert after["remaining_learner"] == control.sampler_rng_telemetry()[
            "remaining_learner"
        ]
        assert after["high_updates"] != before["high_updates"]

        def consume_low_sampler(agent):
            batches = list(
                agent.rollout_buffer.get_discoverer_sampler(
                    1,
                    1,
                    chunk_length=agent.config.k,
                    device=torch.device("cpu"),
                    cache_tensors=False,
                )
            )
            return [
                np.asarray(batch["observations"]).copy()
                for batch in batches
            ]

        updated_batches = consume_low_sampler(updated)
        control_batches = consume_low_sampler(control)
        assert len(updated_batches) == len(control_batches)
        for actual, expected in zip(updated_batches, control_batches):
            np.testing.assert_array_equal(actual, expected)
        assert updated.sampler_rng_telemetry()["remaining_learner"] == control.sampler_rng_telemetry()[
            "remaining_learner"
        ]

        checkpoint_state = copy.deepcopy(updated.sampler_rng_state_dict())
        checkpoint_telemetry = updated.sampler_rng_telemetry()
        consume_low_sampler(updated)
        updated._high_sampler_state = np.random.default_rng(123).bit_generator.state
        updated.load_sampler_rng_state_dict(checkpoint_state)
        assert updated.sampler_rng_telemetry() == checkpoint_telemetry
    finally:
        for env in (*updated_envs, *control_envs):
            env.close()


def test_two_rollout_reset_path_retains_u_contract(tmp_path, spec):
    two = replace(spec, rollouts=2)
    summary = r.run_fit("U", tmp_path / "two-rollout", "technical-check", spec=two, device="cpu")
    assert summary["status"] == "complete"
    assert summary["counts"]["training_transitions"] == 80
    assert summary["counts"]["training_episodes"] == 4
    assert summary["counts"]["native_updates"] == 2
    assert summary["label_flow_checks"]["storage_batches"] == 40
    assert len(summary["d2_retained_work"]) == 2
    assert all(row["decision_rows"] == 4 for row in summary["d2_retained_work"])
    assert summary["native_optimizer_calls"]["coordinator"] == 0


@pytest.mark.skipif(not torch.cuda.is_available(), reason="requires actual CUDA runtime")
def test_actual_cuda_pair_rng_storage_and_two_rollout_contract(tmp_path, spec):
    cuda_spec = replace(spec, rollouts=2)
    summaries = {
        arm: r.run_fit(
            arm,
            tmp_path / f"cuda-{arm}",
            "technical-check",
            spec=cuda_spec,
            device="cuda",
        )
        for arm in ("M", "U")
    }
    learned, uniform = summaries["M"], summaries["U"]
    assert learned["initial_native_digest"] == uniform["initial_native_digest"]
    assert learned["initial_frozen_digest"] == uniform["initial_frozen_digest"]
    assert r.jsonable(learned["panels"]["initial_uniform"]["native_scores_J"]) == r.jsonable(
        uniform["panels"]["initial_uniform"]["native_scores_J"]
    )
    for arm, summary in summaries.items():
        assert summary["status"] == "complete"
        assert summary["counts"]["native_updates"] == 2
        assert len(summary["d2_retained_work"]) == 2
        assert summary["label_flow_checks"]["failures"] == 0
        movement = summary["training_rows"][-1]["relative_initialization_displacement"]
        assert all(
            movement[name] > 0
            for name in (
                "discoverer_actor",
                "discoverer_critic",
                "team_discriminator",
                "individual_discriminator",
            )
        )
        assert all(
            summary["training_rows"][-1]["auxiliary_head_relative_movement"][name] > 0
            for name in ("G", "P")
        )
        checkpoint = torch.load(
            tmp_path / f"cuda-{arm}" / "final.pt",
            map_location="cpu",
            weights_only=False,
        )
        assert checkpoint["rng"]["default_process"]["torch_cuda"] is not None
        assert all(
            body["state"]["torch_cuda"] is not None
            for body in checkpoint["rng"]["private_streams"].values()
        )
        assert set(checkpoint["rng"]["rollout_samplers"]) == {
            "remaining_learner",
            "high_updates",
        }
    assert learned["native_optimizer_calls"]["coordinator"] > 0
    assert uniform["native_optimizer_calls"]["coordinator"] == 0
    assert uniform["training_rows"][-1]["relative_initialization_displacement"][
        "coordinator"
    ] == 0
    assert learned["final_private_rng_streams"]["low_actions"] == uniform[
        "final_private_rng_streams"
    ]["low_actions"]
    assert learned["final_sampler_rng_streams"]["remaining_learner"] == uniform[
        "final_sampler_rng_streams"
    ]["remaining_learner"]
    assert learned["final_sampler_rng_streams"]["high_updates"] != learned[
        "initial_sampler_rng_streams"
    ]["high_updates"]
    assert uniform["final_sampler_rng_streams"]["high_updates"] == uniform[
        "initial_sampler_rng_streams"
    ]["high_updates"]


def test_wrong_u_factor_after_first_32_canonical_rows_fails(tmp_path):
    spec = replace(
        r.DEFAULT_SPEC,
        n_users=8,
        horizon=60,
        lanes=8,
        rollouts=1,
        eval_lanes=2,
        threads=1,
        small_model=True,
    )
    agent, envs = build(tmp_path, spec, "U", suffix="-factor")
    telemetry = r._storage_telemetry()
    try:
        states, observations = b01.native._reset_all(envs)
        env_steps = np.zeros(spec.lanes, np.int64)
        dones = np.zeros(spec.lanes, bool)
        for t in range(spec.horizon):
            actions, _, data = agent.step(
                states,
                observations,
                env_steps,
                dones,
                deterministic=False,
                return_step_data=True,
                build_infos=False,
            )
            next_states, next_obs, rewards, next_dones = [], [], [], []
            for lane, env in enumerate(envs):
                state, obs, reward, done, _, _ = r.physical_step(env, actions[lane])
                next_states.append(state)
                next_obs.append(obs)
                rewards.append(reward)
                next_dones.append(done)
            next_states = np.stack(next_states)
            next_obs = np.stack(next_obs)
            next_dones = np.asarray(next_dones)
            r.store_verified_batch(
                agent,
                telemetry,
                states=states,
                next_states=next_states.copy(),
                observations=observations,
                next_observations=next_obs.copy(),
                actions=actions,
                rewards=np.asarray(rewards),
                dones=next_dones,
                infos_batch=None,
                rollout_step_idx=t,
                step_data=data,
            )
            states, observations, dones = next_states, next_obs, next_dones
            env_steps += 1

        healthy = agent.audit_uniform_d2_storage(spec.horizon)
        assert healthy["canonical_rows_checked"] == 48
        tables = agent.rollout_buffer.get_d2_tables(spec.horizon)
        rows = np.argwhere(np.asarray(tables["team_valid"], dtype=np.bool_))
        assert len(rows) > 32
        time_row, env_row = rows[35]
        agent.rollout_buffer.d2_team_old_log_prob[time_row, env_row] = 0.0
        with pytest.raises(RuntimeError, match="team factor"):
            agent.audit_uniform_d2_storage(spec.horizon)
    finally:
        for env in envs:
            env.close()


def test_private_rng_context_restores_process_and_checkpoint_state(tmp_path, spec):
    r.seed_rng(spec.train_rng_seed)
    before = r.rng_state_digest()
    stream = PersistentProcessRNG(spec.high_update_seed)
    initial = stream.state_dict()
    with stream.use():
        random.random()
        np.random.random()
        torch.rand(3)
    assert r.rng_state_digest() == before
    assert stream.state_dict()["state"]["python"] != initial["state"]["python"]

    restored = PersistentProcessRNG(spec.high_update_seed)
    restored.load_state_dict(stream.state_dict())
    assert restored.digest() == stream.digest()
    with pytest.raises(ValueError, match="seed mismatch"):
        PersistentProcessRNG(spec.high_update_seed + 1).load_state_dict(stream.state_dict())


def test_entry_refuses_unadmitted_call_before_outputs(tmp_path):
    out = tmp_path / "must-not-exist"
    result = subprocess.run(
        [
            sys.executable,
            str(b01.ROOT / "scripts/run_complementary_skill_learning_b04.py"),
            "--arm",
            "U",
            "--seed",
            "260923931",
            "--launch-sha",
            "unadmitted",
            "--out",
            str(out),
        ],
        cwd=b01.ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert not out.exists()


def test_saved_summary_and_jsonl_are_complete(pair):
    root, summaries = pair
    for arm, summary in summaries.items():
        saved = json.loads((root / arm / "summary.json").read_text())
        assert saved["status"] == "complete"
        assert saved["checkpoints"]["final"]["sha256"] == summary["checkpoints"][
            "final"
        ]["sha256"]
        assert saved["training_log"]["rows"] == 1
        assert saved["auxiliary_predictions"]["batches"] == 1
        assert saved["resources"]["durable_output_bytes_excluding_summary"] > 0
        assert saved["resources"]["resources_unmeasured"] == ["peak_scratch_bytes"]
        assert len((root / arm / "training.jsonl").read_text().splitlines()) == 1
        assert len((root / arm / "auxiliary_predictions.jsonl").read_text().splitlines()) == 1
