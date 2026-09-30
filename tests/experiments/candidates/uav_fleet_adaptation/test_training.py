"""Synthetic collector/update checks; no prospective training/evaluation worlds run."""
from dataclasses import replace
from pathlib import Path
import json
import subprocess

import numpy as np
import pytest
import torch

from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from experiments.candidates.agent_count_generalization.adapter import CountAdapter
from experiments.candidates.agent_count_generalization.configuration import DEFAULT_SPEC
from experiments.candidates.agent_count_generalization import runner as shared
from experiments.candidates.uav_fleet_adaptation import host, training


def synthetic_world(world_id):
    if world_id not in (91, 92):
        raise ValueError("explicit synthetic fixture IDs only")
    rng = np.random.RandomState(world_id)
    users = rng.uniform(0., 1000., size=(50, 2))
    positions = rng.uniform(0., 1000., size=(8, 3))
    positions[:, 2] = rng.uniform(50., 150., size=8)
    return host.MatchedWorld(world_id, world_id, world_id + 10, users, positions)


def fixture_env(world_id, horizon=20):
    return CountAdapter(ParallelToArrayAdapter(
        host.FleetS1(world_id, horizon, world_generator=synthetic_world), seed=world_id))


def test_production_world_addresses_member_order_and_rng_isolation():
    assert len(host.TRAIN_WORLD_IDS) == 512 and len(host.EVAL_WORLD_IDS) == 32
    assert set(host.TRAIN_WORLD_IDS).isdisjoint(host.EVAL_WORLD_IDS)
    # World generation is read-only geometry, with no native rollout/exposure.
    world_id = host.TRAIN_WORLD_IDS[0]
    before = training.b03._rng_digest()
    first, second = host.world(world_id), host.world(world_id)
    np.testing.assert_array_equal(first.user_positions, second.user_positions)
    for stream, seed in ((1, first.user_seed), (2, first.uav_seed), (3, host.runtime_seed(world_id))):
        expected = int(np.random.SeedSequence([260930, 17, world_id, stream]).generate_state(1)[0])
        assert seed == expected
    users_rng = np.random.RandomState(first.user_seed)
    np.testing.assert_array_equal(first.user_positions,
                                 [[users_rng.uniform(0, 1000), users_rng.uniform(0, 1000)] for _ in range(50)])
    uav_rng = np.random.RandomState(first.uav_seed)
    np.testing.assert_array_equal(first.uav_positions,
                                 [[uav_rng.uniform(0, 1000), uav_rng.uniform(0, 1000),
                                   uav_rng.uniform(50, 150)] for _ in range(8)])
    assert training.b03._rng_digest() == before
    with pytest.raises(ValueError):
        host.world(91)
    with pytest.raises(ValueError):
        host.runtime_seed(host.TRAIN_WORLD_IDS[-1] + 1)
    assert training.TrainSpec() == training.TrainSpec(32, 16, 500)
    with pytest.raises(ValueError):
        training.TrainSpec(groups=1).validate()


@pytest.fixture(scope="module")
def synthetic_collection(tmp_path_factory):
    torch.set_num_threads(1)
    root = tmp_path_factory.mktemp("fleet-warmstart")
    outputs = {}
    spec = replace(DEFAULT_SPEC, train_n=8, horizon=20, train_lanes=2,
                   hidden_size=16, n_heads=2, n_layers=1, ppo_epochs=1,
                   sequence_batch_size=8, coordinator_batch_size=2)
    for arm in ("A", "F"):
        envs = [fixture_env(world_id) for world_id in (91, 92)]
        before = training.b03._rng_digest()
        pairs = [env.reset(seed=world_id) for env, world_id in zip(envs, (91, 92))]
        assert training.b03._rng_digest() == before
        shared.seed_rng(91)
        config = training.source.make_config("H6", envs, 91, spec)
        agent = training.source.build_agent(config, str(root / arm))
        with torch.no_grad():
            # Make overrange raw Gaussian storage a reliable correctness witness.
            agent.skill_discoverer.actor.act.action_out.logstd._bias.fill_(1.)
        agent.train(True)
        initial = shared.capture_parameters(agent)
        calls, handles = shared.optimizer_counts(agent)
        stored = []
        original_store, original_step = agent.store_transition_batch, agent.step
        action_masks, replay_actions = [], []

        def step(*args, **kwargs):
            action_masks.append([host.mask_integer(env.env.env.transmitter_mask) for env in envs])
            return original_step(*args, **kwargs)

        def store(**kwargs):
            stored.append({name: np.asarray(kwargs[name]).copy() for name in (
                "states", "next_states", "observations", "next_observations", "actions", "rewards", "dones")})
            return original_store(**kwargs)

        original_evaluate = agent.skill_discoverer.actor.evaluate_actions

        def evaluate(*args, **kwargs):
            replay_actions.append(args[2].detach().cpu().numpy().copy())
            return original_evaluate(*args, **kwargs)

        agent.step, agent.store_transition_batch = step, store
        agent.skill_discoverer.actor.evaluate_actions = evaluate
        shared.seed_rng(91)
        try:
            arrays, row, last_states, last_obs, dones = training.collect_group(
                agent, envs, np.stack([info["state"] for obs, info in pairs]),
                np.stack([obs for obs, info in pairs]), arm=arm, world_ids=(91, 92), horizon=20)
            assert not any(calls.values())
            losses, audit = training.audited_update(agent, last_states, last_obs, dones, 20)
            shared.finite(losses, "synthetic update")
            motion = shared.parameter_motion(agent, initial)
            outputs[arm] = arrays, row, stored, action_masks, audit, calls.copy(), motion, replay_actions
            agent.clear_buffers()
            assert not np.any(agent.rollout_buffer.env_lengths) and len(agent.discriminator_buffer) == 0
        finally:
            for handle in handles:
                handle.remove()
            for env in envs:
                env.close()
            if getattr(agent, 'tb_writer', None) is not None:
                agent.tb_writer.close()
    return outputs


def test_old_mask_actor_then_e_and_actual_next_feedback(synthetic_collection):
    for arm, (raw, row, stored, action_masks, *_rest) in synthetic_collection.items():
        assert raw["states"].shape == (21, 2, 133)
        assert raw["observations"].shape == (21, 2, 8, 104)
        assert raw["action_logprobs"].shape == (20, 2, 8)
        np.testing.assert_array_equal(action_masks, raw["old_mask"])
        np.testing.assert_array_equal(raw["actions"], np.clip(raw["raw_actions"], -1., 1.))
        assert (np.abs(raw["raw_actions"]) > 1.).any()
        for t, transition in enumerate(stored):
            for key in ("states", "observations"):
                np.testing.assert_array_equal(transition[key], raw[key][t])
                np.testing.assert_array_equal(transition["next_" + key], raw[key][t + 1])
            np.testing.assert_array_equal(transition["actions"], raw["raw_actions"][t])
            np.testing.assert_array_equal(transition["rewards"], raw["scalar_reward"][t])
            np.testing.assert_array_equal(transition["dones"], raw["dones"][t])
        np.testing.assert_array_equal(raw["skill_changed"],
                                     np.repeat((np.arange(20) % 10 == 0)[:, None], 2, axis=1))
        assert not raw["dones"][:-1].any() and raw["dones"][-1].all()
        assert raw["stored_valid"].all()
        assert len(row["per_world"]) == 2
        if arm == "A":
            assert (raw["mask"] == 255).all() and row["mask_decisions"] == []
        else:
            assert len(row["mask_decisions"]) == 4
            for decision in row["mask_decisions"]:
                assert decision["counts"]["requested_candidates"] == 255
                assert raw["mask"][decision["t"], decision["lane"]] == decision["selected_mask"]
            for t in range(1, 20):
                if t % 10:
                    np.testing.assert_array_equal(raw["mask"][t], raw["mask"][t - 1])
    for key in ("positions", "states", "observations"):
        np.testing.assert_array_equal(synthetic_collection["A"][0][key][0],
                                     synthetic_collection["F"][0][key][0])
    assert (synthetic_collection["F"][0]["mask"] != 255).any()


def test_real_full_h6_update_actual_exposure_and_movement(synthetic_collection):
    for raw, row, stored, action_masks, audit, calls, motion, replay in synthetic_collection.values():
        assert audit["optimizer_calls"] == calls
        assert calls == {"coordinator": 2, "discoverer_actor": 4, "discoverer_critic": 4,
                         "team_discriminator": 1, "individual_discriminator": 4}
        assert audit["discoverer"]["sample_presentations"] == 320
        assert audit["discoverer"]["valid_presentations"] == 320
        assert audit["coordinator"]["sample_presentations"] == 4
        assert audit["discriminator"]["team"]["records"] == 40
        assert audit["discriminator"]["team"]["sample_presentations"] == 40
        assert audit["discriminator"]["individual"]["records"] == 320
        assert audit["discriminator"]["individual"]["sample_presentations"] == 320
        assert all(motion[key]["delta_l2"] > 0 for key in shared.OPTIMIZERS)
        assert len(replay) == 4
        assert any((np.abs(batch) > 1.).any() for batch in replay)
        # Sampler reordering preserves the exact raw collected action multiset.
        collected_rows = np.sort(raw["raw_actions"].reshape(-1, 3), axis=0)
        replay_rows = np.sort(np.concatenate([batch.reshape(-1, 3) for batch in replay]), axis=0)
        np.testing.assert_array_equal(replay_rows, collected_rows)


def test_parent_metadata_survives_sparse_snapshot_and_remains_bound(tmp_path, monkeypatch):
    checkpoint_root = Path("temp/directions/uav_fleet_adaptation/inputs").resolve()
    if not (checkpoint_root / training.PARENT.tag / "checkpoint_45.pt").exists():
        pytest.skip("retained parent external checkpoint is not staged on this host")
    original = training.PARENT_SUMMARY_ROOT / training.PARENT.tag / "summary.json"
    # A disposable Git fixture tests the frozen loader's real HEAD-byte check.
    # It contains only the bound metadata, with no historical runs/ working file.
    repository = tmp_path / "metadata-binding"
    metadata_root = repository / "experiments/candidates/uav_fleet_adaptation/inputs"
    metadata = metadata_root / training.PARENT.tag / "summary.json"
    metadata.parent.mkdir(parents=True)
    metadata.write_bytes(original.read_bytes())
    def git(*args):
        return subprocess.run(
            ["git", "-C", str(repository), "-c", "core.hooksPath=/dev/null", *args],
            check=True, capture_output=True)
    git("init", "-q")
    git("add", str(metadata.relative_to(repository)))
    git("-c", "user.name=Binding test", "-c", "user.email=binding@example.invalid",
        "commit", "-qm", "Bind retained metadata")
    monkeypatch.setattr(training, "REPOSITORY_ROOT", repository)
    monkeypatch.setattr(training, "PARENT_SUMMARY_ROOT", metadata_root)
    assert not (repository / training.PARENT_SUMMARY_ORIGIN["path"]).exists()
    record = training.load_parent(checkpoint_root)
    assert record["summary_identity"]["working_bytes_identical"] is True
    assert record["summary_identity"]["sha256"] == training.PARENT_SUMMARY_SHA256
    assert record["summary_identity"]["origin"] == training.PARENT_SUMMARY_ORIGIN
    assert record["checkpoint_sha256_before"] == record["checkpoint_record"]["sha256"]
    metadata.write_bytes(metadata.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="pinned original"):
        training.load_parent(checkpoint_root)
    metadata.write_bytes(original.read_bytes())
    git("rm", "--cached", str(metadata.relative_to(repository)))
    git("-c", "user.name=Binding test", "-c", "user.email=binding@example.invalid",
        "commit", "-qm", "Remove committed binding")
    with pytest.raises(ValueError, match="not committed at HEAD"):
        training.load_parent(checkpoint_root)


def test_retained_parent_restoration_is_strict_and_fresh(tmp_path):
    checkpoint_root = Path("temp/directions/uav_fleet_adaptation/inputs")
    if not (checkpoint_root / training.PARENT.tag / "checkpoint_45.pt").exists():
        pytest.skip("retained parent external checkpoint is not staged on this host")
    record = training.load_parent(checkpoint_root)
    before = training.b03._rng_digest()
    agent, config, initialization = training.build_warmstart(record, tmp_path / "logs")
    try:
        assert training.b03._rng_digest() == before
        assert initialization["parameter_normalizer_digest"] == record["summary"]["final_parameter_normalizer_digest"]
        assert all(value == 0 for value in initialization["optimizer_state_entries"].values())
        assert initialization["discriminator_records"] == 0
        assert not np.any(initialization["buffer_env_lengths"])
        assert config.n_agents == 8 and config.batch_size == config.discriminator_batch_size == 16000
        assert not getattr(config, "disable_high_level_training", False)
        assert not getattr(config, "disable_discriminator_training", False)
        assert not config.use_obsnorm and not config.use_statenorm
        assert not agent.training
        # Endpoint restoration uses the same strict module/normalizer API.
        with torch.no_grad():
            next(agent.skill_discoverer.actor.parameters()).add_(.001)
        expected_digest = shared.digest_agent(agent)
        binding = training.save_endpoint(agent, tmp_path, config, "synthetic-checkpoint-test")
        path = tmp_path / binding["path"]
        assert training.source.file_sha256(path) == binding["sha256"]
        payload = torch.load(path, map_location="cpu", weights_only=True)
        assert payload["direction"] == "uav_fleet_adaptation" and payload["rollout"] == 32
        restored, restored_config, endpoint = training.build_warmstart(record, tmp_path / "endpoint", payload=payload)
        assert endpoint["parameter_normalizer_digest"] == expected_digest
        assert all(value == 0 for value in endpoint["optimizer_state_entries"].values())
        assert training.b03._rng_digest() == before
    finally:
        if getattr(agent, 'tb_writer', None) is not None:
            agent.tb_writer.close()


def test_partial_failed_collection_keeps_actual_native_and_storage_counts(tmp_path, monkeypatch):
    """Inject a failure after one lane of the first batch was actually stored."""
    torch.set_num_threads(1)
    spec = replace(DEFAULT_SPEC, train_n=8, train_lanes=16, hidden_size=16,
                   n_heads=2, n_layers=1, ppo_epochs=1)
    envs = []

    def make_fixture(world_id, horizon):
        env = fixture_env(91, horizon)
        envs.append(env)
        return env

    def build_fixture(record, log_dir):
        shape = training.SimpleNamespace(n_uavs=8, state_dim=133, obs_dim=104)
        config = training.source.make_config("H6", [shape] * 16, 91, spec)
        agent = training.source.build_agent(config, str(log_dir))
        original = agent.store_transition_batch

        def fail_store(**kwargs):
            # Use genuine native+learner storage, then represent failure after
            # only one lane completed, exercising reconciliation from the buffer.
            original(**kwargs)
            agent.rollout_buffer.env_lengths[1:] = 0
            raise RuntimeError("injected partial store failure")

        agent.store_transition_batch = fail_store
        return agent, config, {"synthetic": True}

    monkeypatch.setattr(training, "make_env", make_fixture)
    monkeypatch.setattr(training, "build_warmstart", build_fixture)
    with pytest.raises(RuntimeError, match="injected partial store"):
        training.train_arm("A", {"checkpoint_record": {}}, tmp_path / "fit", "synthetic-failure-test")
    result = json.loads((tmp_path / "fit" / "summary.json").read_text())
    assert result["status"] == "failed" and result["fit_started"]
    assert result["counts"]["training_team_steps"] == 16
    assert result["counts"]["stored_team_steps"] == 1
    assert result["counts"]["actor_calls"] == 1
    assert result["counts"]["training_episodes"] == 0
    assert result["counts"]["updates"] == result["counts"]["update_attempts"] == 0
    assert not any(result["optimizer_calls"].values())
    assert result["rollouts"][0]["status"] == "failed"
