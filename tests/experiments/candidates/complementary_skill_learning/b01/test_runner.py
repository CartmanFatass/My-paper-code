from dataclasses import replace
import json
from pathlib import Path
import pickle
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.complementary_skill_learning.b01 import runner as r


@pytest.fixture
def small_spec():
    return replace(r.DEFAULT_SPEC, n_users=8, horizon=30, lanes=2, rollouts=1,
                   eval_lanes=2, diagnostic_lanes=1, prefix_steps=10, threads=1, small_model=True)


@pytest.fixture
def small_agent(tmp_path, small_spec):
    from experiments.candidates.complementary_skill_learning.b01.learning import ComplementaryAgent
    torch.set_num_threads(1)
    envs = r.make_envs(small_spec, small_spec.lanes, small_spec.train_world_base)
    cfg = r.make_config(small_spec, envs)
    r.seed_rng(small_spec.init_seed)
    agent = ComplementaryAgent(config=cfg, arm="D", head_seed=small_spec.head_seed,
                               aux_seed=small_spec.aux_seed, log_dir=str(tmp_path / "logs"),
                               device=torch.device("cpu"))
    yield agent, envs
    for env in envs:
        env.close()


def test_signed_pairing_uses_prediction_and_same_marginals():
    good = r.signed_pairing([.6, .2, .2, .6], [.6, .2, .2, .6])
    wrong = r.signed_pairing([.2, .6, .6, .2], [.6, .2, .2, .6])
    assert good["T"] == pytest.approx(.2)
    assert wrong["T"] == pytest.approx(-.2)
    assert good["matched_value"] == pytest.approx(.6)
    assert good["independent_value"] == pytest.approx(.4)
    assert good["preference_reversal"]
    additive = r.signed_pairing([1, 0, 0, 1], [4, 7, 6, 9])
    assert additive["T"] == 0
    offset = r.signed_pairing([1, 0, 0, 1], [10.6, 10.2, 10.2, 10.6])
    assert offset["T"] == pytest.approx(good["T"])


def test_execution_clip_preserves_raw_sample():
    class Env:
        def step(self, action):
            self.executed = action.copy()
            return np.zeros((6, 3)), .1, False, False, {
                "next_state": np.zeros(4), "reward_components": {
                    "reward_info": dict.fromkeys(r.COMPONENTS, 0.)}}
    env = Env()
    raw = np.full((6, 3), 2., np.float32)
    original = raw.copy()
    r.physical_step(env, raw)
    np.testing.assert_array_equal(raw, original)
    np.testing.assert_array_equal(env.executed, np.ones_like(raw))


def test_manual_frozen_executor_matches_real_native_step(small_agent, small_spec):
    agent, envs = small_agent
    agent.train(False)
    states, obs = r.native._reset_all(envs)
    hidden = np.zeros((small_spec.lanes, 6, agent.config.gru_hidden_size), np.float32)
    labels = np.random.default_rng(37)
    for t in range(20):
        native_actions, _, data = agent.step(states, obs, np.full(small_spec.lanes, t),
                                             np.zeros(small_spec.lanes, bool), deterministic=True,
                                             return_step_data=True, build_infos=False)
        if t % 10 == 0:
            teams, skills = r.select_skills(agent, states, obs, "own", labels)
        np.testing.assert_array_equal(teams, data["team_skills"])
        np.testing.assert_array_equal(skills, data["agent_skills"])
        manual_actions, hidden = r.low_actions(agent, obs, skills, hidden, deterministic=True)
        np.testing.assert_array_equal(manual_actions, native_actions)
        np.testing.assert_array_equal(hidden, agent.actor_hidden_np[:small_spec.lanes])
        for lane, env in enumerate(envs):
            states[lane], obs[lane], *_ = r.physical_step(env, native_actions[lane])


def test_native_snapshot_common_innovations_and_branch_order(small_agent, small_spec):
    agent, envs = small_agent
    agent.train(False)
    states, obs = r.native._reset_all(envs)
    env = envs[0]
    hidden = np.zeros((6, agent.config.gru_hidden_size), np.float32)
    # Populate recurrent state, connection state and geometry caches before snapshotting.
    for _ in range(small_spec.prefix_steps):
        raw, next_hidden = r.low_actions(agent, obs[:1], np.arange(6)[None], hidden[None], deterministic=True)
        states[0], obs[0], *_ = r.physical_step(env, raw[0])
        hidden = next_hidden[0]
    original = pickle.dumps(env)
    before_rng = torch.get_rng_state().clone()
    a, b = r.rectangles()[0]["cells"][:2]
    first = r.execute_branch(agent, env, states[0], obs[0], hidden, a, small_spec, 281)
    other = r.execute_branch(agent, env, states[0], obs[0], hidden, b, small_spec, 281)
    second = r.execute_branch(agent, env, states[0], obs[0], hidden, a, small_spec, 281)
    assert first == second
    assert pickle.dumps(env) == original
    assert torch.equal(before_rng, torch.get_rng_state())
    assert len(first["rewards"]) == 10 and len(other["rewards"]) == 10
    # The first physical outcome follows the recorded raw draw under exactly one clip.
    np.testing.assert_array_equal(np.clip(first["raw_actions"], -1, 1), first["executed_actions"])


def test_evaluation_preserves_rng_weights_and_training_hidden(small_agent, small_spec):
    agent, _ = small_agent
    before_weights = r.frozen_digest(agent)
    before_torch = torch.get_rng_state().clone()
    before_numpy = pickle.dumps(np.random.get_state())
    before_state = pickle.dumps(agent.env_hidden_states)
    panel = r.evaluate_panel(agent, small_spec, small_spec.own_initial_base, "own")
    assert panel["transitions"] == 60 and panel["optimizer_calls"] == 0
    np.testing.assert_allclose(panel["native_scores_J"], panel["component_means"]["total_reward"])
    assert r.frozen_digest(agent) == before_weights
    assert torch.equal(before_torch, torch.get_rng_state())
    assert pickle.dumps(np.random.get_state()) == before_numpy
    assert pickle.dumps(agent.env_hidden_states) == before_state


@pytest.mark.parametrize("device", ["cpu", pytest.param("cuda", marks=pytest.mark.skipif(
    not torch.cuda.is_available(), reason="requires actual CUDA runtime"))])
def test_real_three_arm_fit_matches_initial_facts_and_retains_outputs(tmp_path, small_spec, device):
    summaries = []
    for arm in ("D", "G", "P"):
        out = tmp_path / arm
        summary = r.run_fit(arm, out, "technical-check", spec=small_spec, device=device)
        summaries.append(summary)
        assert summary["status"] == "complete"
        assert summary["counts"]["training_transitions"] == 60
        assert summary["counts"]["stored_transitions"] == 60
        assert summary["counts"]["training_episodes"] == 2
        assert summary["counts"]["evaluation_transitions"] == 350
        assert summary["counts"]["native_updates"] == 1
        assert all(x > 0 for x in summary["native_optimizer_calls"].values())
        assert all(x > 0 for x in summary["training_rows"][-1]["relative_initialization_displacement"].values())
        assert len(summary["auxiliary_history"]) == 1
        predictions = [json.loads(line) for line in (out / "auxiliary_predictions.jsonl").read_text().splitlines()]
        assert len(predictions) == 1 and predictions[0]["rollout"] == 1
        assert (out / "initial.pt").is_file() and (out / "final.pt").is_file()
        diag = json.loads((out / "combination_diagnostic.json").read_text())
        assert len(diag["rows"]) == 4
        assert diag["optimizer_calls"] == 0 and diag["transitions"] == 170
        assert json.loads((out / "summary.json").read_text())["status"] == "complete"
    assert len({x["initial_native_digest"] for x in summaries}) == 1
    assert len({x["first_rollout_facts_sha256"] for x in summaries}) == 1
    assert len({x["auxiliary_history"][0]["raw_target_sha256"] for x in summaries}) == 1
    calibration = [x["auxiliary_history"][0]["target_calibration"] for x in summaries]
    assert calibration[0] == calibration[1] == calibration[2]
    assert [x["auxiliary_history"][0]["trunk_optimizer_steps"] for x in summaries] == [0, 1, 1]


def test_entry_refuses_unadmitted_call_before_outputs(tmp_path):
    out = tmp_path / "must-not-exist"
    result = subprocess.run([sys.executable, str(r.ROOT / "scripts/run_complementary_skill_learning_b01.py"),
                             "--arm", "D", "--seed", "260923901", "--launch-sha", "unadmitted",
                             "--out", str(out)], cwd=r.ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode != 0
    assert not out.exists()


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA RNG isolation needs actual CUDA runtime")
def test_cuda_rng_is_preserved():
    before = [x.clone() for x in torch.cuda.get_rng_state_all()]
    with r.preserve_rng():
        torch.randn((3, 4), device="cuda")
    assert all(torch.equal(a, b) for a, b in zip(before, torch.cuda.get_rng_state_all()))
