import json
from functools import partial
from types import SimpleNamespace

import gymnasium as gym
import numpy as np
import pytest
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv
import torch

from experiments.candidates.uav_persistent_service.batch import choose_action
from experiments.candidates.uav_persistent_service.constants import TRAIN_SEEDS, EVAL_SEEDS, lane_seeds, plan
from experiments.candidates.uav_persistent_service.controllers import FEATURE_DIM
from experiments.candidates.uav_persistent_service.macro_env import NativeEpisode, NativeMacroEnv
from experiments.candidates.uav_persistent_service.policy import CommitmentDistribution, CommitmentPolicy
from experiments.candidates.uav_persistent_service.readout import PAIR_FIELDS, RISK_FIELDS, summarize
from experiments.candidates.uav_persistent_service.training import POLICY_KWARGS, PPO_PARAMS, TrainingAudit, attach_gradient_audit, optimizer_steps


class WiringEnv(gym.Env):
    observation_space = gym.spaces.Box(-np.inf, np.inf, (FEATURE_DIM,), dtype=np.float32)
    action_space = gym.spaces.Discrete(25)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.t = 0
        obs = np.zeros(FEATURE_DIM, np.float32)
        obs[:8] = 1
        return obs, {}

    def step(self, action):
        self.t += 1
        obs = np.zeros(FEATURE_DIM, np.float32)
        obs[:8] = self.t % 2
        return obs, float(int(action) == 0), self.t == 4, False, {}


def make_model():
    torch.set_num_threads(1)
    return PPO(CommitmentPolicy, WiringEnv(), **PPO_PARAMS, policy_kwargs=POLICY_KWARGS)


def test_semantic_law_mask_ties_and_finite_gradients():
    logits = torch.zeros((3, 33), requires_grad=True)
    mask = torch.tensor([[1]*8, [0, 1]+[0]*6, [0]*8], dtype=torch.bool)
    law = CommitmentDistribution(25).proba_distribution(logits, mask)
    np.testing.assert_allclose(law.distribution.probs[0, 0].item(), .5)
    np.testing.assert_allclose(law.distribution.probs[0, 1:].detach(), np.full(24, 1/48), rtol=1e-6)
    assert law.mode().tolist() == [0, 0, 0]
    assert law.distribution.probs[2, 0] == 1
    assert torch.count_nonzero(law.distribution.probs[2, 1:]) == 0
    loss = -(law.log_prob(torch.tensor([1, 4, 0])) + .01 * law.entropy()).mean()
    loss.backward()
    assert torch.isfinite(logits.grad).all()
    assert torch.count_nonzero(logits.grad[2]) == 0
    changed = logits.detach().clone()
    changed[:, 0] = -.01
    law.proba_distribution(changed, mask)
    assert law.mode().tolist() == [1, 4, 0]
    # Staged deployment deliberately differs from flattened joint argmax.
    assert law.distribution.probs[0].argmax().item() == 0


def test_policy_roundtrip_and_one_synthetic_optimizer_step(tmp_path):
    model = make_model()
    features, _ = WiringEnv().reset()
    assert int(model.predict(features, deterministic=True)[0]) == 0
    path = tmp_path / "initial.zip"
    model.save(path)
    restored = PPO.load(path, device="cpu")
    assert int(restored.predict(features, deterministic=True)[0]) == 0
    model.n_steps = 4
    model.batch_size = 4
    model.n_epochs = 1
    model.rollout_buffer.buffer_size = 4
    model.rollout_buffer.reset()
    gradient_state, hook = attach_gradient_audit(model.policy, tmp_path/"gradients.jsonl")
    model.learn(total_timesteps=4)
    hook.remove()
    assert optimizer_steps(model.policy) == 1
    assert gradient_state["pre_step_records"] == 1
    assert json.loads((tmp_path/"gradients.jsonl").read_text())["finite"]
    assert all(torch.isfinite(value).all() for value in model.policy.state_dict().values())
    np.testing.assert_array_equal(model.rollout_buffer.rewards[:, 0],
                                  (model.rollout_buffer.actions.reshape(-1) == 0).astype(np.float32))
    # Last finite episode reward has no learned continuation contribution.
    assert model.rollout_buffer.returns.reshape(-1)[-1] == model.rollout_buffer.rewards[-1, 0]


def test_actual_evaluator_initial_l_equals_p_and_native_macro_exhaustion(tmp_path):
    model = make_model()
    p = NativeEpisode(70301, "P", horizon=60)
    initial = NativeEpisode(70301, "L", horizon=60)
    try:
        while not p.done:
            a, statistics = choose_action(initial, model)
            assert a == 0
            p.macro_step(0)
            initial.macro_step(a, statistics)
        for key in ("reward", "native_post_xyz", "submitted", "native_battery", "user_xy_m"):
            np.testing.assert_array_equal(p.arrays()[key], initial.arrays()[key])
        assert p.pairing.digests() == initial.pairing.digests()
        assert p.row()["service_snapshot_calls"] == initial.row()["service_snapshot_calls"]
        saved = initial.save(tmp_path / "trace.npz", complete=True)
        assert saved["raw_bytes"] > 0
        assert json.loads((tmp_path / "trace.decisions.json").read_text())["complete"]
    finally:
        p.close()
        initial.close()
    env = NativeMacroEnv([70302], horizon=30)
    try:
        env.reset()
        _, reward, terminated, truncated, info = env.step(0)
        assert terminated and not truncated and not info["TimeLimit.truncated"]
        assert reward == info["native_reward_sum"]
        env.reset()
        assert env.counts()["exhausted"] and env.counts()["native_steps"] == 30
        with pytest.raises(RuntimeError, match="beyond"):
            env.step(0)
    finally:
        env.close()


def test_fixed_schedule_and_no_partial_contrast():
    assert set(TRAIN_SEEDS).isdisjoint(EVAL_SEEDS)
    assert sorted(seed for lane in range(4) for seed in lane_seeds(lane)) == list(TRAIN_SEEDS)
    assert len(plan()) == 48
    assert summarize([], plan())["contrasts"] == {}
    assert summarize([], plan())["status"] == "incomplete"


def test_complete_reader_blocks_pairing_mismatch_and_additional_risk():
    jobs = [dict(arm=arm, seed=seed, job_key=f"{arm}/{seed}") for seed in (1,2) for arm in ("L", "O", "P")]
    rows = [job | dict(status="completed", actual_length=3000, raw_native_J=10 if job["arm"] == "L" else 0,
                      horizon_normalized_qos=.6 if job["arm"] == "L" else .5,
                      native_reserve_uav_step_fraction=0,
                      **{key: 0 for key in RISK_FIELDS}, **{key: str(job["seed"]) for key in PAIR_FIELDS})
            for job in jobs]
    rows[0]["final300_persistent_reserve_members"] = 1
    result = summarize(rows, jobs)
    assert result["status"] == "complete"
    assert result["practical"]["L-P"]["mean_service_threshold_pass"]
    assert result["practical"]["L-P"]["default_use_blocked"]
    rows[0]["user_xy_trace_sha256"] = "different"
    result = summarize(rows, jobs)
    assert result["status"] == "incomplete" and result["pairing_failures"]
    assert not result["contrasts"] and not result["practical"]


def test_production_training_audit_with_synthetic_complete_rollout(tmp_path):
    (tmp_path/"training").mkdir()
    model = make_model()
    audit = TrainingAudit(tmp_path)
    audit.model = SimpleNamespace(policy=model.policy, num_timesteps=400)
    audit._on_rollout_start()
    features = torch.zeros((4, FEATURE_DIM))
    features[:, :8] = 1
    for t in range(100):
        infos = [dict(world_seed=70400+lane, macro_start=t*30, macro_native_steps=30,
                      native_reward_sum=float(t+lane), **{"TimeLimit.truncated": False},
                      choice=dict(requested_action=0, executed_action=0, eligible=True),
                      native_episode=dict(actual_length=3000, seed=70400+lane,
                                          raw_native_J=0., qos_per_step=0.)) for lane in range(4)]
        audit.locals = dict(infos=infos, actions=np.zeros(4), obs_tensor=features,
                            log_probs=torch.full((4,), -np.log(2)), dones=np.ones(4, bool))
        assert audit._on_step()
    audit.model.rollout_buffer = SimpleNamespace(full=True,
        rewards=np.asarray(audit.rewards, np.float32),
        actions=np.asarray(audit.actions, np.float32)[..., None])
    audit._on_rollout_end()
    assert audit.rollouts == 1 and audit.exposure_rows == 400
    audit.model.rollout_buffer.rewards[0,0] = -999
    with pytest.raises(RuntimeError, match="stored requested"):
        audit._on_rollout_end()


def test_commitment_reading_keeps_allocation_and_release_distinct():
    from experiments.candidates.uav_persistent_service.mechanisms import commitment_readings
    arrays = {key: np.zeros((5,8)) for key in ("charging", "native_charger_input_wh", "native_consumed_wh",
        "native_positive_net_charge_wh", "native_charging_eligible", "native_battery", "mode", "entered", "native_load")}
    arrays.update(commit_active=np.ones((5,8)), reward=np.zeros(5),
                  native_pre_xyz=np.zeros((5,8,3)), native_post_xyz=np.zeros((5,8,3)),
                  submitted=np.zeros((5,8,4)), proposed=np.zeros((5,8,4)), initial_native_battery=np.zeros(8))
    for key in ("charging", "mode", "entered", "native_charging_eligible"):
        arrays[key] = arrays[key].astype(bool)
    arrays["charging"][1:3,0] = True
    arrays["native_charging_eligible"][1:4,0] = True
    arrays["native_charger_input_wh"][1:3,0] = .25
    arrays["native_post_xyz"][4,0,0] = 1
    events = [dict(kind="start", member=0, step=0, duration=120, station=0),
              dict(kind="arrival", member=0, step=1),
              dict(kind="release", member=0, step=4, reason="full"),
              dict(kind="assignment_restored", member=0, step=4)]
    options, aggregate = commitment_readings(arrays, events)
    row = options[0]
    assert row["allocated_charging_steps"] == 2 and row["native_eligible_wait_steps"] == 1
    assert row["charging_interruptions"] == 1 and row["charger_input_wh"] == .5
    assert row["dwell_elapsed"] == 3 and row["assignment_restored"] == 4
    assert row["first_free_actual_move"] == 4 and row["first_post_release_connected_load"] is None
    assert aggregate["commitment_full_releases"] == 1
    # Release, assignment, and readmission can share a timestamp; event order owns them.
    events.extend([dict(kind="start", member=0, step=4, duration=600, station=0),
                   dict(kind="censored", member=0, step=5)])
    options, aggregate = commitment_readings(arrays, events)
    assert len(options) == 2
    assert options[0]["stop"] == 4 and options[0]["release_reason"] == "full"
    assert options[0]["assignment_restored"] == 4
    assert options[1]["start"] == 4 and options[1]["stop"] == 5
    assert options[1]["release_reason"] is None and options[1]["end_kind"] == "censored"
    assert options[1]["assignment_restored"] is None


def test_four_native_spawn_lanes_exhaust_without_repeating_worlds():
    vec = SubprocVecEnv([partial(NativeMacroEnv, [70310+lane], lane=lane, horizon=30)
                        for lane in range(4)], start_method="spawn")
    try:
        obs = vec.reset()
        assert obs.shape == (4, FEATURE_DIM)
        _, rewards, dones, infos = vec.step(np.zeros(4, dtype=int))
        assert dones.all()
        np.testing.assert_array_equal(rewards, np.asarray([info["native_reward_sum"] for info in infos]))
        counts = vec.env_method("counts")
        assert all(row["native_steps"] == 30 and row["exhausted"] for row in counts)
        assert all(info["choice"]["requested_action"] == 0 and not info["TimeLimit.truncated"] for info in infos)
    finally:
        vec.close()


def test_evaluator_preserves_partial_failure(monkeypatch, tmp_path):
    from experiments.candidates.uav_persistent_service import batch
    job = dict(arm="O", seed=70320, job_key="O/70320")
    class FailingEpisode(NativeEpisode):
        def __init__(self, seed, arm):
            super().__init__(seed, arm, horizon=60)
        def macro_step(self, action, statistics=None):
            super().macro_step(action, statistics)
            raise RuntimeError("intentional collection failure")
    monkeypatch.setattr(batch, "plan", lambda: [job])
    monkeypatch.setattr(batch, "NativeEpisode", FailingEpisode)
    (tmp_path / "raw").mkdir()
    row = batch.worker((job, str(tmp_path), None))
    assert row["status"] == "failed" and row["partial_observed_steps"] == 30
    assert "intentional" in row["error"]
    with np.load(tmp_path / row["raw_path"]) as raw:
        assert len(raw["reward"]) == 30
    assert not json.loads((tmp_path / row["decisions_path"]).read_text())["complete"]
