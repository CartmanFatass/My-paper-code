from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.agent_count_generalization.action_law_b03 import runner as b03
from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.configuration import DEFAULT_SPEC
from experiments.candidates.agent_count_generalization.local_ordinary_b16 import runner as b16
from experiments.candidates.agent_count_generalization.ordered_roster_confirmation_b20.runner import Arm
from experiments.candidates.agent_count_generalization.runner import digest_agent, native_components
from experiments.candidates.controller_composition.b01.bindings import CHECKPOINT_ROOT, SOURCE
from experiments.candidates.controller_composition.b01.runner import (
    _identity, _service, restore_runtime, route_actions, validate_sources,
)


@pytest.fixture(scope="module")
def sources():
    paths = {n: Path(CHECKPOINT_ROOT) / entry["tag"] / "F/raw/checkpoint_45.pt"
             for n, entry in SOURCE.items()}
    payloads, dependencies = validate_sources(paths)
    assert len(dependencies) >= 20
    return payloads


def test_real_checkpoint_restore_rejects_tamper_and_keeps_normalizers(sources, tmp_path):
    envs = make_envs(1, 81, 6, 500)
    try:
        config = b16.make_b16_config(Arm("F", SOURCE[1]["seed"]), envs, DEFAULT_SPEC, expected_n=6)
        agent = restore_runtime(config, sources[1]["checkpoint"], sources[1]["expected_digest"], tmp_path / "logs")
        before = digest_agent(agent)
        assert before == sources[1]["expected_digest"]
        agent.reset_env_state(0)
        assert digest_agent(agent) == before
        with pytest.raises(ValueError, match="forbidden"):
            agent.store_transition_batch(None)
        with pytest.raises(ValueError, match="forbidden"):
            agent.discoverer_actor_optimizer.step()
        assert digest_agent(agent) == before
        altered = dict(sources[1]["checkpoint"])
        altered["config"] = {**altered["config"], "n_agents": 3}
        # Config/file mismatch is checked before any runtime construction.
        assert altered["config"] != sources[1]["published_config"]["config"]
        with pytest.raises(ValueError, match="published source"):
            restore_runtime(config, sources[1]["checkpoint"], "0" * 64, tmp_path / "bad")
        third_config = b16.make_b16_config(Arm("F", SOURCE[3]["seed"]), envs,
                                              DEFAULT_SPEC, expected_n=6)
        third = restore_runtime(third_config, sources[3]["checkpoint"],
                                sources[3]["expected_digest"], tmp_path / "third")
        assert digest_agent(third) == sources[3]["expected_digest"]
    finally:
        for env in envs:
            env.close()


def test_ordered_homogeneous_route_matches_native_path_on_two_fixture_steps(sources, tmp_path):
    # One nonproduction world, two transitions. Both independent full N6 runtimes
    # observe the same actual mixed-env inputs; source B20's clipping is the comparator.
    envs = make_envs(1, 81, 6, 500)
    try:
        config = b16.make_b16_config(Arm("F", SOURCE[1]["seed"]), envs, DEFAULT_SPEC, expected_n=6)
        agents = [restore_runtime(config, sources[1]["checkpoint"], sources[1]["expected_digest"],
                                  tmp_path / f"logs-{side}") for side in range(2)]
        assert agents[0] is not agents[1]
        for agent in agents:
            agent.reset_env_state(0)
        obs, info = envs[0].reset()
        state = info["state"][None]
        observations = obs[None]
        assert list(envs[0].env.agents) == list(envs[0].env.env.possible_agents)
        initial = _identity(state)
        steps, dones = np.zeros(1, dtype=np.int64), np.zeros(1, dtype=bool)
        before = [digest_agent(agent) for agent in agents]
        with torch.no_grad():
            for _ in range(2):
                raw = [agent.step(state, observations, steps, dones, deterministic=True,
                                  return_step_data=True, build_infos=False)[0] for agent in agents]
                np.testing.assert_array_equal(raw[0], raw[1])
                joined = route_actions(*raw)
                np.testing.assert_array_equal(joined, raw[0])
                executed = b03.map_training_actions(joined, "clip")
                np.testing.assert_array_equal(executed, b03.map_training_actions(raw[0], "clip"))
                obs, reward, term, trunc, info = envs[0].step(executed[0])
                parts = native_components(info, reward, 6)
                e, s, u, height = _service(envs[0], parts)
                assert 0 <= s <= e <= 50 and u == e - s and np.isfinite(height)
                assert np.isclose(6 * reward, .7 * parts["coverage_reward"] +
                                  .3 * parts["quality_reward"] - parts["energy_penalty"])
                state, observations = info["next_state"][None], obs[None]
                steps += 1
                dones[:] = term or trunc
        assert not dones.any()
        assert [digest_agent(agent) for agent in agents] == before
        # A separate construction/reset of this fixture seed reproduces its scene.
        replica = make_envs(1, 81, 6, 500)[0]
        try:
            _, replica_info = replica.reset()
            assert _identity(replica_info["state"][None]) == initial
        finally:
            replica.close()
    finally:
        for env in envs:
            env.close()


def test_route_rejects_shortcut_and_keeps_native_roles():
    a = np.arange(18, dtype=np.float32).reshape(1, 6, 3)
    b = a + 100
    joined = route_actions(a, b)
    np.testing.assert_array_equal(joined[0, :3], a[0, :3])
    np.testing.assert_array_equal(joined[0, 3:], b[0, 3:])
    with pytest.raises(ValueError, match="full-roster"):
        route_actions(a[:, :3], b[:, :3])


def test_checkpoint_and_config_mismatch_are_rejected_before_runtime(sources, monkeypatch, tmp_path):
    from experiments.candidates.controller_composition.b01 import runner
    paths = {n: Path(CHECKPOINT_ROOT) / entry["tag"] / "F/raw/checkpoint_45.pt"
             for n, entry in SOURCE.items()}
    paths[1] = tmp_path / "wrong.pt"
    paths[1].write_bytes(b"invalid checkpoint")
    with pytest.raises(ValueError, match="checkpoint hash mismatch"):
        runner.validate_sources(paths)
    paths[1] = Path(CHECKPOINT_ROOT) / SOURCE[1]["tag"] / "F/raw/checkpoint_45.pt"
    load = runner.torch.load
    def changed_config(*args, **kwargs):
        payload = load(*args, **kwargs)
        payload["config"] = {**payload["config"], "n_agents": 3}
        return payload
    monkeypatch.setattr(runner.torch, "load", changed_config)
    with pytest.raises(ValueError, match="checkpoint/config mismatch"):
        runner.validate_sources(paths)


def test_entry_requires_admission_before_result_work(monkeypatch, tmp_path):
    from scripts import run_controller_composition_b01 as entry
    calls = []
    monkeypatch.setattr(entry, "require_admission", lambda *args, **kwargs: calls.append("admit") or {"sha": "accepted"})
    def fake_run(out, sha, admission, paths, **kwargs):
        calls.append("run")
        assert calls == ["admit", "run"]
        assert sha == admission["sha"] and kwargs["seed"] == 92_525_000
        assert not out.exists()
    argv = ["--launch-sha", "accepted", "--out", str(tmp_path / "result"),
            "--checkpoint-root", str(tmp_path / "checkpoints")]
    entry.main(argv, run_fn=fake_run)
    assert calls == ["admit", "run"]
    with pytest.raises(ValueError, match="launch SHA"):
        entry.main(["--launch-sha", "wrong", *argv[2:]], run_fn=fake_run)
    assert calls == ["admit", "run", "admit"]


def test_two_sources_keep_private_lane_and_role_hidden_state(sources, tmp_path):
    envs = make_envs(2, 81, 6, 500)
    try:
        pairs = [env.reset() for env in envs]
        states = np.stack([info["state"] for _, info in pairs])
        observations = np.stack([obs for obs, _ in pairs])
        agents = []
        for source in (1, 2):
            config = b16.make_b16_config(Arm("F", SOURCE[source]["seed"]), envs,
                                         DEFAULT_SPEC, expected_n=6)
            agents.append(restore_runtime(config, sources[source]["checkpoint"],
                                          sources[source]["expected_digest"], tmp_path / f"source{source}"))
        with torch.no_grad():
            for agent in agents:
                agent.step(states, observations, np.zeros(2, dtype=np.int64),
                           np.zeros(2, dtype=bool), deterministic=True,
                           return_step_data=True, build_infos=False)
        first, second = agents
        first_lane1 = first.actor_hidden_np[1].copy()
        second_lane0 = second.actor_hidden_np[0].copy()
        second_lane1 = second.actor_hidden_np[1].copy()
        assert np.any(first.actor_hidden_np[0]) and np.any(first_lane1)
        first.reset_env_state(0)
        np.testing.assert_array_equal(first.actor_hidden_np[0], 0)
        np.testing.assert_array_equal(first.actor_hidden_np[1], first_lane1)
        np.testing.assert_array_equal(second.actor_hidden_np[0], second_lane0)
        np.testing.assert_array_equal(second.actor_hidden_np[1], second_lane1)
    finally:
        for env in envs:
            env.close()


def test_integrated_fixture_two_cells_share_initial_worlds_and_emit_native_raw(sources, monkeypatch, tmp_path):
    from experiments.candidates.controller_composition.b01 import runner
    monkeypatch.setattr(runner, "WORLDS", (81, 82))
    monkeypatch.setattr(runner, "HORIZON", 2)
    (tmp_path / "raw").mkdir()
    homogeneous = runner._eval_cell(1, 1, sources, tmp_path)
    mixed = runner._eval_cell(1, 2, sources, tmp_path)
    reverse = tmp_path / "reverse"
    (reverse / "raw").mkdir(parents=True)
    mixed_first = runner._eval_cell(1, 2, sources, reverse)
    homogeneous_second = runner._eval_cell(1, 1, sources, reverse)
    assert homogeneous["initial_world_identity"] == mixed["initial_world_identity"]
    assert homogeneous["initial_world_identity"] == mixed_first["initial_world_identity"]
    assert homogeneous["initial_world_identity"] == homogeneous_second["initial_world_identity"]
    assert homogeneous["initial_world_identity_per_world"] == mixed_first["initial_world_identity_per_world"]
    assert homogeneous["native_agent_rows"] == mixed["native_agent_rows"]
    assert homogeneous["counts"] == mixed["counts"]
    assert mixed["counts"]["team_steps"] == 4
    assert mixed["counts"]["executed_uav_action_rows"] == 24
    assert mixed["counts"]["inferred_policy_action_rows"] == 48
    with np.load(tmp_path / mixed["raw_artifact"]["path"]) as trace:
        assert trace["executed_actions"].shape == (2, 2, 6, 3)
        np.testing.assert_array_equal(trace["executed_actions"][:, :, :3],
                                      np.clip(trace["source_i_raw_actions"][:, :, :3], -1, 1))
        np.testing.assert_array_equal(trace["executed_actions"][:, :, 3:],
                                      np.clip(trace["source_j_raw_actions"][:, :, 3:], -1, 1))
        np.testing.assert_allclose(trace["S"], 50 * trace["coverage_reward"])
        np.testing.assert_allclose(trace["U"], trace["E"] - trace["S"])
