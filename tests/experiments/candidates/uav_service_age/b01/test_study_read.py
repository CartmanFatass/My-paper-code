import numpy as np
import pytest
import torch

from experiments.candidates.uav_service_age.b01 import study, read, run
from experiments.candidates.uav_service_age.b01.features import FEATURE_DIM
from experiments.candidates.uav_service_age.b01.learner import Learner, parameter_digest
from experiments.candidates.uav_service_age.b01.scheduler import Scheduler
from experiments.candidates.uav_registered_service.b02 import study as retained


def collect(tmp_path, arm, seed, horizon=8, **kwargs):
    env = study.factory(seed)
    env.env.max_steps = horizon
    out = tmp_path / f'{arm}-{seed}-{horizon}'
    (out / 'raw').mkdir(parents=True)
    counts = dict(explicit_resets=0, native_step_calls=0, team_steps=0, complete_episodes=0)
    try:
        row, raw = study.collect_episode(env, arm, seed, out, counts, horizon=horizon,
                                         selector=lambda features: np.array([.5, .5]), **kwargs)
        study.save_episode(out, row, raw)
    finally:
        env.close()
    return row, raw, counts


def test_all_seven_programs_native_reading_and_retained_equivalence(tmp_path, monkeypatch):
    # Seven complete8-tick fixtures plus three retained8-tick equivalence traces =80 steps.
    saved = {}
    for arm in study.ARMS:
        row, raw, counts = collect(tmp_path, arm, 77101)
        saved[arm] = (row, raw)
        assert counts['team_steps'] == 8 and counts['complete_episodes'] == 1
        result = read.verify_episode(row, raw, selector=lambda features: np.array([.5, .5]))
        assert result['verified_steps'] == 8
        assert row['A'] == raw['actual_ages'].mean()
        if arm in study.NEW_ARMS:
            assert raw['age_features'].shape == (2, FEATURE_DIM)
            assert raw['forecast_lengths'].tolist() == [4, 2]
    for arm in ('O', 'G', 'S2'):
        env = study.factory(77101)
        env.env.max_steps = 8
        out = tmp_path / f'original-{arm}'
        (out / 'raw').mkdir(parents=True)
        counts = dict(explicit_resets=0, native_step_calls=0, team_steps=0, complete_episodes=0)
        try:
            original = retained.collect_episode(env, arm, 77101, out, counts, horizon=8)
        finally:
            env.close()
        raw = read.load_episode(original['raw']['path'])
        timing = {'c_wall','c_cpu','scheduler_wall','scheduler_cpu','history_wall','history_cpu',
                  'prefix_wall','prefix_cpu','candidate_wall','candidate_cpu','terminal_history_wall',
                  'terminal_history_cpu','gate_wall','gate_cpu'}
        for key in raw:
            if key not in timing:
                np.testing.assert_array_equal(saved[arm][1][key], raw[key])
    from envs.pettingzoo.uav_env import MultiUAVEnv
    def forbid(*args, **kwargs):
        raise AssertionError('pure reader created a native episode')
    monkeypatch.setattr(MultiUAVEnv, '__init__', forbid)
    monkeypatch.setattr(MultiUAVEnv, 'step', forbid)
    row, raw = saved['M']
    read.verify_episode(row, raw)
    for field in ('actual_ages', 'age_features', 'model_contacts', 'age_candidate_age_costs',
                  'age_plan_costs', 'choice_innovations'):
        corrupt = {key: value.copy() for key, value in raw.items()}
        if field == 'age_candidate_age_costs':
            q, mask = raw['candidate_order'][0, 0]
            corrupt[field][0, q, mask] += 1
        elif field == 'model_contacts':
            corrupt[field][0, 0] = ~corrupt[field][0, 0]
        else:
            corrupt[field].flat[0] += 1
        with pytest.raises(AssertionError):
            read.verify_episode(row, corrupt)


def test_first_missing_report_causal_critic_and_full_plan_hold(tmp_path):
    class FirstMissing(Scheduler):
        def decide(self, *args, **kwargs):
            if args[3] == 0:
                kwargs['started'] -= 10
            return super().decide(*args, **kwargs)
    row, raw, counts = collect(tmp_path, 'L0', 77102, horizon=12, scheduler_type=FirstMissing)
    assert counts['team_steps'] == 12
    assert not raw['timely'][0] and raw['terminal_history_start'] == 4
    assert not raw['model_valid'][:4].any()
    assert raw['age_forced_before_sampling'][0] and not raw['age_sampled'][0]
    assert raw['age_feature_availability'][0].tolist() == [False] * 5
    np.testing.assert_array_equal(raw['commitments'][0], raw['commands'][0])
    read.verify_episode(row, raw, selector=lambda features: np.array([.5, .5]))


def test_full_horizon_sampled_network_terminal_and_no_within_episode_update(tmp_path):
    # One fixed initialized policy trajectory (0 fits) checks all64 slots/terminal.
    learner = Learner(FEATURE_DIM, seed=77103)
    before = parameter_digest(learner.actor), parameter_digest(learner.critic)
    env = study.factory(77103)
    env.env.max_steps = 256
    out = tmp_path / 'full'
    (out / 'raw').mkdir(parents=True)
    counts = dict(explicit_resets=0, native_step_calls=0, team_steps=0, complete_episodes=0)
    try:
        row, raw = study.collect_episode(env, 'L0', 77103, out, counts, selector=learner.probabilities)
    finally:
        env.close()
    assert counts['team_steps'] == 256
    assert before == (parameter_digest(learner.actor), parameter_digest(learner.critic))
    assert learner.actor_updates == learner.critic_updates == 0
    assert raw['age_features'].shape == (64, FEATURE_DIM)
    assert raw['forecast_lengths'][-1] == 2
    assert np.isnan(raw['forecast'][-1, :, 2:]).all()
    result = read.verify_episode(row, raw, selector=learner.probabilities)
    assert result['verified_steps'] == result['verified_model_transitions'] == 256
    assert result['candidate_physics_pairs'] >= raw['candidate_plans'][[0,15,31,63]].sum()
    assert abs(raw['report_rewards'].sum() + row['A']) < 1e-12


def test_fixed_source_streams_and_admission_before_effects(tmp_path, monkeypatch):
    assert study.TRAIN_EPISODES == 512 and study.WORLDS == 64
    config = study.frozen_config('fixture')
    assert config['planned_episodes'] == 960 and config['planned_steps'] == 245760
    assert len(set(config['train_seeds'] + config['evaluation_seeds'])) == 576
    for position in range(7):
        for arm in study.ARMS:
            assert sum(order[position] == arm for order in study.ARM_ORDERS) == 2
    from scripts import hmasd_admission
    def refuse(*args, **kwargs):
        assert kwargs['direction'] == 'uav_service_age'
        raise RuntimeError('fixture admission refusal')
    monkeypatch.setattr(hmasd_admission, 'require_admission', refuse)
    with pytest.raises(RuntimeError, match='fixture admission refusal'):
        run.main(['--out', str(tmp_path / 'missing'), '--launch-sha', 'fixture', '--seed', '29311000'])
    assert not (tmp_path / 'missing').exists()
    with pytest.raises(SystemExit):
        run.main(['--out', str(tmp_path / 'missing'), '--launch-sha', 'fixture', '--seed', '77104'])


def test_update_failure_preserves_completed_raw_and_partial_update_counts(tmp_path, monkeypatch):
    # Pure orchestration fixture: no environment, native transition or actual optimizer.
    class FakeEnv:
        env = type('Inner', (), {})()
        def close(self):
            pass
    class FailingLearner:
        def __init__(self, input_dim):
            self.actor, self.critic = torch.nn.Linear(1, 2), torch.nn.Linear(1, 1)
            self.actor_updates = self.critic_updates = 0
        def probabilities(self, features):
            return np.array([.5, .5])
        def state(self):
            return dict(actor=self.actor.state_dict(), critic=self.critic.state_dict())
        def update(self, *args):
            self.actor_updates, self.critic_updates = 2, 1
            raise RuntimeError('fixture update failure')
    def fake_episode(env, arm, seed, out, counts, **kwargs):
        counts['complete_episodes'] += 1
        raw = dict(age_features=np.zeros((64, FEATURE_DIM), np.float32),
                   age_sampled_choice=np.zeros(64, int), age_logp=np.zeros(64),
                   age_sampled=np.zeros(64, bool), report_rewards=np.zeros(64))
        return dict(arm=arm, seed=seed), raw
    monkeypatch.setattr(study, 'TRAIN_SEED', 77104)
    monkeypatch.setattr(study, 'factory', lambda seed: FakeEnv())
    monkeypatch.setattr(study, 'Learner', FailingLearner)
    monkeypatch.setattr(study, 'collect_episode', fake_episode)
    monkeypatch.setattr(torch, 'set_num_interop_threads', lambda count: None)
    summary = study.run_batch(tmp_path / 'failure', 'fixture')
    assert summary['status'] == 'INCOMPLETE_TECHNICAL_FAILURE'
    assert summary['counts']['actor_updates'] == 2 and summary['counts']['critic_updates'] == 1
    assert summary['counts']['training_episodes'] == 0 and summary['counts']['native_step_calls'] == 0
    failed = summary['failed_training_episode']
    raw = read.load_episode(failed['raw']['path'])
    assert str(raw['learner_failure_type']) == 'RuntimeError'
    assert str(raw['learner_failure_message']) == 'fixture update failure'
    assert 'actor_before_sha256' in raw and raw['age_features'].shape == (64, FEATURE_DIM)
    read.verified_artifact(summary['failed_checkpoint'])
