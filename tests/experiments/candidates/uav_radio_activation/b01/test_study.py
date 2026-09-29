from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.uav_radio_activation.b01 import protocol as p
from experiments.candidates.uav_radio_activation.b01 import study
from experiments.candidates.uav_radio_activation.b01.scheduler import Scheduler


class DeterministicScheduler(Scheduler):
    def __init__(self, arm, packet):
        super().__init__(arm, packet, clock=lambda: 0.0)


def test_native_arrival_preserves_completed_reward_and_masks(tmp_path):
    env = study.factory(713)
    env.env.max_steps = 8
    out = tmp_path / 'run'
    (out / 'raw').mkdir(parents=True)
    counts = dict(explicit_resets=0, native_step_calls=0, team_steps=0, complete_episodes=0)
    row = study.collect_episode(env, 'E', 713, out, counts, horizon=8,
                                scheduler_type=DeterministicScheduler)
    with np.load(row['raw']['path']) as raw:
        assert raw['mask'][0] == 31
        assert np.all(raw['mask'][1:5] == raw['applied_mask'][0])
        assert np.all(raw['mask'][5:] == raw['applied_mask'][1])
        assert np.all(raw['selected_mask'] == raw['applied_mask'])
        for tick in range(8):
            np.testing.assert_array_equal(np.isfinite(raw['sinr'][tick]).any(axis=1), p.mask_array(raw['mask'][tick]))
            assert raw['served'][tick] == raw['connections'][tick].sum()
            assert raw['reward'][tick] == pytest.approx(.7 * raw['served'][tick] / 50 + .3 * raw['quality'][tick])
        for tick in range(1, 8):
            muted = ~p.mask_array(raw['mask'][tick])
            assert np.all(raw['observations'][tick, muted, 3:103] == 0)
        # New commands in reports must match this round, not a prior held command.
        for index, tick in enumerate((0, 4)):
            _, commands = p.decode_reports([x.tobytes() for x in raw['report_packets'][index]], tick)
            np.testing.assert_array_equal(commands, raw['commands'][tick])
        from experiments.candidates.uav_radio_activation.b01.read import verify_episode
        reading = verify_episode(row, raw, verify_observations=False)
        assert reading['verified_steps'] == 8
        assert reading['max_native_J_error'] < 1e-12
    assert counts == dict(explicit_resets=1, native_step_calls=8, team_steps=8, complete_episodes=1)
    env.close()


def test_arm_order_balanced_and_complete_pair_required():
    for position in range(3):
        order = [study.ARM_ORDERS[i % 6][position] for i in range(64)]
        counts = [order.count(arm) for arm in study.ARMS]
        assert max(counts) - min(counts) <= 1
    with pytest.raises(ValueError):
        study.paired_reading([], [713])


def test_offline_observation_reconstruction():
    from experiments.candidates.uav_radio_activation.b01.read import observed_rows
    env = study.factory(714)
    for mask in (31, 7, 1):
        observed = env.env.set_transmitter_mask(p.mask_array(mask))
        expected = observed_rows(env.env.uav_positions, env.env.user_positions, mask, 0)
        actual = env._dict_to_array(observed)
        np.testing.assert_allclose(expected, actual, atol=1e-6, rtol=0)
    env.close()


def test_resource_ceiling_preserves_incomplete_raw(tmp_path, monkeypatch):
    calls = [0]

    def ceiling():
        calls[0] += 1
        if calls[0] == 3:
            raise study.ResourceLimit('fixture CPU ceiling')

    def short_env(seed):
        env = study.factory(seed)
        env.env.max_steps = 8
        return env

    monkeypatch.setattr(study, 'check_cpu', ceiling)
    result = study.run_batch(tmp_path / 'incomplete', 'fixture', make_env=short_env,
                             seeds=(715,), horizon=8)
    assert result['status'] == 'INCOMPLETE_RESOURCE_LIMIT'
    assert result['counts']['team_steps'] == 1 and result['counts']['complete_episodes'] == 0
    assert 'paired' not in result and len(result['artifacts']) == 1
    with np.load(result['artifacts'][0]['path']) as raw:
        assert raw['completed_steps'] == 1


def test_runner_requires_admission_before_output(tmp_path, monkeypatch):
    from experiments.candidates.uav_radio_activation.b01 import run
    from scripts import hmasd_admission

    def refuse(*args, **kwargs):
        raise RuntimeError('fixture admission refused')

    monkeypatch.setattr(hmasd_admission, 'require_admission', refuse)
    out = tmp_path / 'no-output'
    with pytest.raises(RuntimeError, match='fixture admission refused'):
        run.main(['--out', str(out), '--launch-sha', 'fixture', '--seed', '29305000'])
    assert not out.exists()
