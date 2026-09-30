"""Bounded synthetic/pure-formula checks; no native pilot or result launch."""
import hashlib
import subprocess
import sys

import numpy as np
import pytest

from experiments.candidates.uav_local_history.b01.controller import (
    LocalController, _parse, _power, COMMANDS, NOISE,
)
from experiments.candidates.uav_local_peer_forecast.controller import MotionController, associate
from experiments.candidates.uav_local_peer_forecast import reader, study
from envs.pettingzoo import uav_radio

TEST_SEED = 7  # Correctness identity only; never a member of the scientific panel.


def fixture_geometry():
    """Handcrafted grid, independent of production seeded initialization."""
    positions = np.array(((120., 140., 60.), (260., 170., 80.), (600., 400., 110.),
                          (850., 850., 90.), (880., 870., 120.)))
    users = np.array([(40.+185*(i % 5), 45.+95*(i // 5)) for i in range(50)])
    return positions, users


def row(t, own=(400., 400., 80.), peers=(), users=((340., 340.),), sinr=10.):
    own = np.asarray(own)
    value = np.zeros(104, dtype=np.float32)
    value[:3] = (own[0]/1000, own[1]/1000, (own[2]-50)/100)
    for i, user in enumerate(users):
        value[3+3*i:6+3*i] = (*((np.asarray(user)-own[:2])/1000), (sinr+10)/50)
    for i, peer in enumerate(peers):
        value[63+4*i:67+4*i] = (*((np.asarray(peer)-own)/(1000, 1000, 100)), .4)
    value[103] = t/256
    return value


@pytest.mark.parametrize('arm', ('V', 'R'))
def test_own_motion_sorting_clock_hold_and_reset(arm):
    actor = MotionController(arm)
    old = ((650., 450., 80.), (150., 450., 80.))
    actor.act(row(0, peers=old), 0)
    command, _ = actor.act(row(1, own=(430., 400., 80.), peers=old[::-1]), 1)
    np.testing.assert_array_equal(actor.delta, 0)
    np.testing.assert_array_equal(actor.matches, (1, 0))
    np.testing.assert_array_equal(command, actor._command)
    moved = ((650., 450., 110.), (120., 450., 80.))
    held = actor._command.copy()
    actor.act(row(2, peers=moved), 2)
    np.testing.assert_allclose(actor.delta, ((0, 0, 30), (-30, 0, 0)), atol=.001)
    np.testing.assert_array_equal(actor._command, held)
    with pytest.raises(ValueError, match='clock'):
        actor.act(row(2), 2)
    with pytest.raises(ValueError, match='clock'):
        actor.act(row(4), 4)
    with pytest.raises(ValueError, match='clock'):
        actor.act(row(3), True)
    actor.reset()
    assert actor._clock == -1 and actor._nav_index is None and not actor._previous_peers.size
    assert not any(actor.counters.values())
    actor.act(row(0, peers=moved), 0)
    np.testing.assert_array_equal(actor.delta, 0)


def test_ambiguity_gates_snap_clip_missing_reappearance():
    previous = np.array(((100., 100., 80.), (115., 100., 80.)))
    current = np.array(((105., 100., 80.),))
    matches, delta, gates = associate(current, previous)
    np.testing.assert_array_equal(matches, (-1,))
    np.testing.assert_array_equal(delta, 0)
    np.testing.assert_array_equal(gates, (2,))
    matches, _, _ = associate(previous, current)
    np.testing.assert_array_equal(matches, (-1, -1))  # column ambiguity
    previous = np.array(((100., 100., 80.),))
    current = np.array(((130.0005, 99.9995, 50.),))
    matches, delta, _ = associate(current, previous)
    np.testing.assert_array_equal(matches, (0,))
    np.testing.assert_array_equal(delta, ((30., 0., -30.),))
    assert associate(np.array(((130.002, 100., 80.),)), previous)[0][0] == -1
    actor = MotionController('V')
    actor.act(row(0, peers=previous), 0)
    actor.act(row(1, peers=()), 1)
    actor.act(row(2, peers=current), 2)
    np.testing.assert_array_equal(actor.matches, (-1,))
    np.testing.assert_array_equal(actor.delta, 0)


@pytest.mark.parametrize('arm', ('V', 'R'))
@pytest.mark.parametrize('empty_users', (False, True))
def test_exact_inactive_parity_near_boundaries_and_private_state(arm, empty_users):
    c, candidate = LocalController(False), MotionController(arm)
    peers = ((1000.00005, 5., 49.99998),)
    users = () if empty_users else ((960., 10.), (10., 20.))
    for t in range(12):
        obs = row(t, own=(1000., 0., 50.), peers=peers, users=users)
        pristine = obs.copy()
        ca, cd = c.act(obs.copy(), t)
        va, vd = candidate.act(obs, t)
        np.testing.assert_array_equal(obs, pristine)
        np.testing.assert_array_equal(ca, va)
        assert c._nav_index == candidate._nav_index
        if t % 4 == 0:
            np.testing.assert_array_equal(cd['scores'], vd['scores'])
            np.testing.assert_array_equal(cd['served_candidates'], vd['served_candidates'])
        assert not candidate.counters['moving_link_evaluations']
    other = MotionController(arm)
    assert other._clock == -1 and other._nav_index is None


@pytest.mark.parametrize('arm', ('V', 'R'))
def test_active_to_inactive_counts_mixed_stationary_no_clipping(arm, monkeypatch):
    import experiments.candidates.uav_local_peer_forecast.controller as live
    actor = MotionController(arm)
    stationary = (1000.00005, 900., 49.99998)
    calls = []
    original = live._power

    def capture(stations, users):
        calls.append(np.array(stations, copy=True))
        return original(stations, users)

    monkeypatch.setattr(live, '_power', capture)
    for t in range(5):
        moving = (600.+min(t, 4)*30, 450., 120.)
        command, diagnostic = actor.act(row(t, peers=(moving, stationary)), t)
    # One setup, four moving-only peer evaluations, one own-candidate batch.
    assert len(calls) == 6
    assert all(a.shape == (1, 3) for a in calls[1:5])
    np.testing.assert_allclose(calls[0][2], stationary, atol=.001)
    assert calls[0][2, 0] > 1000 and calls[0][2, 2] < 50
    assert actor.counters['moving_link_evaluations'] == 4
    own, users, sinr, peers = _parse(row(4, peers=(moving, stationary)))
    prepared = reader.prepare_score(own, users, sinr, peers)
    expected = reader.ranking(prepared, actor.delta, 1 if arm == 'V' else -1,
                              actor._nav_index)
    np.testing.assert_allclose(diagnostic['scores'], expected['scores'], rtol=0, atol=2e-12)
    for t in range(5, 9):
        actor.act(row(t, peers=(moving, stationary)), t)
    counts = actor.counters
    assert counts['moving_link_evaluations'] == 4
    assert counts['link_evaluations'] == (counts['candidate_link_evaluations']
                                        + counts['setup_link_evaluations']+4)


def test_empty_users_with_moving_peer_exact_C_sweep_and_ties():
    c, v = LocalController(False), MotionController('V')
    for t in range(8):
        obs = row(t, own=(100., 100., 50.), peers=((600.+t*30, 400., 80.),), users=())
        command_c, diag_c = c.act(obs.copy(), t)
        command_v, diag_v = v.act(obs.copy(), t)
        np.testing.assert_array_equal(command_c, command_v)
        assert c._nav_index == v._nav_index == 1  # one waypoint advance, held thereafter
        if t % 4 == 0:
            np.testing.assert_array_equal(diag_c['scores'], diag_v['scores'])
            assert diag_v['fallback']
    assert v.counters['moving_link_evaluations'] == 0


def test_scalar_calibration_radio_and_four_sequential_clips():
    own, users, sinr, peers = _parse(row(4, own=(990., 15., 145.), peers=((300., 400., 80.),)))
    prepared = reader.prepare_score(own, users, sinr, peers)
    q = int(np.flatnonzero((COMMANDS == (1., -1., 1.)).all(axis=1))[0])
    np.testing.assert_array_equal(prepared['trajectories'][q], np.tile((1000., 0., 150.), (4, 1)))
    for tx, station in enumerate(np.concatenate((own[None], peers))):
        distance = np.sqrt((station[0]-users[0, 0])**2+(station[1]-users[0, 1])**2+station[2]**2)
        scalar = 10**((23.-20*np.log10(distance)-20*np.log10(4*np.pi/.15))/10)
        assert prepared['present'][tx, 0] == pytest.approx(scalar, rel=1e-14)
    gamma = 10**(sinr[0]/10)
    expected = max(prepared['present'][0, 0]/gamma-prepared['present'][1, 0]-NOISE, 0.)
    assert prepared['unknown'][0] == expected
    # Four visible peers mean no fitted unknown residual regardless of supplied SINR.
    all_peers = np.tile(peers, (4, 1))
    assert not reader.prepare_score(own, users, sinr, all_peers)['unknown'].any()
    delta = np.array(((30., -30., 30.),))
    for sign in (-1, 0, 1):
        result = reader.ranking(prepared, delta, sign, 3)
        assert result['moving_powers'] == (4 if sign else 0)
        assert result['entering_nav'] == 3
        assert prepared['trajectories'][q, 0, 2] == 150


def test_native_radio_formulas_sorting_and_inputs_without_native_step():
    positions, users = fixture_geometry()
    result = reader.native_radio(positions, users, 4)
    loss = uav_radio.free_space_user_path_loss(positions, users)
    native_sinr = uav_radio.user_sinr_from_path_loss(loss)
    np.testing.assert_allclose(result['sinr'], native_sinr, rtol=0, atol=2e-12)
    connections = uav_radio.greedy_connection_assignment(native_sinr)
    np.testing.assert_array_equal(result['connections'], connections)
    metrics = uav_radio.service_metrics(native_sinr, connections)
    assert result['J'] == metrics['J']
    # Exercise current observation builder on a bare object: no constructor, reset or step.
    from envs.pettingzoo.uav_env import MultiUAVEnv
    base = MultiUAVEnv.__new__(MultiUAVEnv)
    base.uav_positions, base.user_positions = positions, users
    base.area_size, base.height_range, base.current_step, base.max_steps = 1000, (50, 150), 4, 256
    base.max_observed_users, base.max_observed_uavs, base.min_sinr = 20, 10, 3.
    base.sinr_matrix = native_sinr
    pd = np.linalg.norm(positions[:, None]-positions[None], axis=-1)
    peer_loss = 20*np.log10(np.maximum(pd, 1e-6))+20*np.log10(4*np.pi/.15)
    np.fill_diagonal(peer_loss, 0.)
    base._uav_uav_path_loss_matrix = peer_loss
    base.tx_power, base.noise_power, base.use_fdma, base.enable_transmitter_mask = 23., -80., False, False
    base.uav_sinr_matrix = base._compute_uav_uav_sinr_matrix()
    for i in range(5):
        np.testing.assert_array_equal(base._get_observation_vectorized(f'uav_{i}')['obs'], result['obs'][i])


class SavedFixture:
    """Pure deterministic radio fixture for collector/reader wiring, never native env."""
    def __init__(self, horizon=8, fail_at=None):
        self.horizon, self.fail_at = horizon, fail_at

    def reset(self, seed):
        assert seed == TEST_SEED
        self.positions, self.users = fixture_geometry()
        self.t = 0
        return reader.native_radio(self.positions, self.users, 0)['obs'], {
            'state_info': dict(uav_positions=self.positions.copy(), user_positions=self.users.copy())}

    def step(self, commands):
        if self.t == self.fail_at:
            raise RuntimeError('fixture injected failure')
        self.positions = np.clip(self.positions+30*commands, reader.LOW, reader.HIGH)
        self.t += 1
        radio = reader.native_radio(self.positions, self.users, self.t)
        info = dict(state_info=dict(uav_positions=self.positions.copy()),
                    rewards_dict={f'uav_{i}': radio['J']/5 for i in range(5)},
                    infos_dict={'uav_0': {'global': dict(connections=radio['connections'],
                                                       sinr_matrix=radio['sinr'], served_users=radio['served'])}})
        return radio['obs'], radio['J']/5, self.t == self.horizon, False, info


def count_fixture():
    return dict(started_episodes=0, explicit_resets=0, actor_ingests=0,
                rankings=0, native_steps=0, complete_episodes=0)


@pytest.mark.parametrize('arm', study.ARMS)
def test_collector_and_independent_reader_complete_fixture(tmp_path, monkeypatch, arm):
    (tmp_path/'raw').mkdir()
    counts = count_fixture()
    episode = study.collect_episode(SavedFixture(), arm, TEST_SEED, tmp_path, counts, horizon=8)
    assert counts == dict(started_episodes=1, explicit_resets=1, actor_ingests=40,
                          rankings=10, native_steps=8, native_steps_attempted=8, complete_episodes=1)
    with np.load(episode['raw']['path'], allow_pickle=False) as saved:
        data = {k: saved[k] for k in saved.files}
    # Candidate scoring disabled after collection: saved-data proof cannot invoke it.
    def forbidden(*args, **kwargs):
        raise AssertionError('live policy/scorer called by reader')
    monkeypatch.setattr(LocalController, 'act', forbidden)
    monkeypatch.setattr(LocalController, '_score', forbidden)
    result, _ = reader.read_episode(data, horizon=8, verify_seed=False)
    assert result['counts']['score_requests'] == (10 if arm == 'C' else 20)
    assert result['counts']['own_power_values'] == sum(int(data['n'][t].sum())*108 for t in (0, 4))
    assert result['endpoint']['J'] == float(data['reward'].mean())
    assert result['worker_counts'] == episode['controller_counts']
    for field, location in (('scores', (0, 0, 0)), ('observations', (0, 0, 0)),
                            ('commands', (1, 0, 0)), ('nav_after', (0, 0)),
                            ('reward', (0,)), ('counters', (0, 0))):
        corrupted = {k: v.copy() for k, v in data.items()}
        corrupted[field][location] += 1
        with pytest.raises(ValueError):
            reader.read_episode(corrupted, horizon=8, verify_seed=False)


def test_failed_collection_preserves_actual_partial_counts_and_raw(tmp_path):
    (tmp_path/'raw').mkdir()
    counts = count_fixture()
    with pytest.raises(RuntimeError, match='injected'):
        study.collect_episode(SavedFixture(fail_at=3), 'R', TEST_SEED, tmp_path, counts, horizon=8)
    assert counts['complete_episodes'] == 0 and counts['native_steps'] == 3
    assert counts['actor_ingests'] == 20
    assert counts['native_steps_attempted'] == 4
    with np.load(tmp_path/'raw'/f'R_{TEST_SEED}.npz') as data:
        assert data['observations'].shape[0] == 4 and data['commands'].shape[0] == 4
        with pytest.raises(ValueError, match='incomplete'):
            reader.read_episode(data, horizon=8, verify_seed=False)


def test_fixed_paired_signed_statistics_no_posthoc_filtering():
    rows = []
    for seed in study.SEEDS:
        for arm, offset in (('C', 0.), ('V', -1.), ('R', 2.)):
            rows.append(dict(seed=seed, arm=arm, endpoint=dict(J=offset, mean_served=offset)))
    result = reader.paired(rows)
    assert result['R-C']['J']['positive'] == 32
    assert result['V-C']['J']['negative'] == 32
    assert result['R-V']['J']['mean'] == 3
    assert result['R-C']['J']['descriptive_t95_df31'] == [2., 2.]
    with pytest.raises(ValueError, match='complete'):
        reader.paired(rows[:-1])
    assert [study.ORDERS[i % 6] for i in range(6)] == list(study.ORDERS)


def test_error_aggregation_mean_euclidean_not_RMS():
    errors = reader.empty_errors()
    errors['all']['pairs'] = 2
    errors['all']['lead_sums'][:] = (2, 4, 6, 8)
    value = reader.error_reading(errors)['all']
    assert value['four_lead_then_pair_mean_m']['C'] == 2.5
    assert value['per_lead_mean_m']['R'] == [1., 2., 3., 4.]
    assert reader.longest_zero_run((0, 0, 1, 0, 0, 0)) == 3


def test_runner_missing_admission_has_no_output_or_native_effect(tmp_path):
    output = tmp_path/'refused'
    import os
    env = os.environ.copy()
    env.pop('HMASD_ADMISSION_V1', None)
    completed = subprocess.run([sys.executable, str(study.ROOT/'experiments/candidates/uav_local_peer_forecast/run.py'),
                                '--launch-sha', '0'*40, '--out', str(output)],
                               env=env, capture_output=True, text=True)
    assert completed.returncode != 0 and 'missing HMASD admission' in completed.stderr
    assert not output.exists()


def test_source_manifest_protects_shared_bytes(monkeypatch):
    import experiments.candidates.uav_local_peer_forecast.study as binding
    def recorded(argv, cwd):
        relative = argv[-1].split(':', 1)[1]
        return (binding.ROOT/relative).read_bytes()
    monkeypatch.setattr(binding.subprocess, 'check_output', recorded)
    manifest = binding.source_binding('0'*40)
    assert len(manifest) == len(binding.SOURCE_PATHS)
    assert {r['path'] for r in manifest} == set(binding.SOURCE_PATHS)
    for item in manifest:
        assert item['sha256'] == hashlib.sha256((binding.ROOT/item['path']).read_bytes()).hexdigest()
    monkeypatch.setitem(binding.FROZEN_BLOBS, 'envs/pettingzoo/uav_radio.py', '0'*40)
    with pytest.raises(RuntimeError, match='frozen shared source changed'):
        binding.source_binding('0'*40)


def test_admitted_precreated_output_no_overwrite_and_failed_status(tmp_path, monkeypatch):
    from experiments.candidates.uav_local_peer_forecast import run
    import scripts.hmasd_admission as admission
    tmp_path.joinpath('launch-manifest.json').write_text('launcher-owned evidence')
    monkeypatch.setattr(admission, 'require_admission', lambda *a, **k: {'sha': '0'*40})
    monkeypatch.setattr(study, 'source_binding', lambda sha: [])
    def fail_factory(seed):
        raise RuntimeError('fixture stopped before native constructor')
    monkeypatch.setattr(study, 'make_real', fail_factory)
    monkeypatch.setattr(sys, 'argv', ['run.py', '--launch-sha', '0'*40, '--out', str(tmp_path)])
    with pytest.raises(RuntimeError, match='fixture stopped'):
        run.main()
    import json
    status = json.loads((tmp_path/'worker-status.json').read_text())
    assert status['status'] == 'failed'
    assert status['counts']['constructors_started'] == 1 and status['counts']['native_steps'] == 0
    assert not (tmp_path/'summary.json').exists()
    assert (tmp_path/'launch-manifest.json').read_text() == 'launcher-owned evidence'
    with pytest.raises(FileExistsError, match='scientific output'):
        run.prepare_output(tmp_path)


def test_source_binding_failure_precedes_output_and_factory(tmp_path, monkeypatch):
    from experiments.candidates.uav_local_peer_forecast import run
    import scripts.hmasd_admission as admission
    monkeypatch.setattr(admission, 'require_admission', lambda *a, **k: {'sha': '0'*40})
    def fail_binding(sha):
        raise RuntimeError('fixture source mismatch')
    monkeypatch.setattr(study, 'source_binding', fail_binding)
    def forbidden(seed):
        raise AssertionError('factory reached before source binding')
    monkeypatch.setattr(study, 'make_real', forbidden)
    output = tmp_path/'uncreated'
    monkeypatch.setattr(sys, 'argv', ['run.py', '--launch-sha', '0'*40, '--out', str(output)])
    with pytest.raises(RuntimeError, match='source mismatch'):
        run.main()
    assert not output.exists()


@pytest.mark.parametrize('corrupt', ('late_score', 'late_counter'))
def test_reader_failure_retains_prior_episode_and_current_work(tmp_path, monkeypatch, corrupt):
    """Exercise standalone failure output after verified earlier fixture episodes."""
    import json
    (tmp_path/'raw').mkdir()
    episodes = [study.collect_episode(SavedFixture(), arm, TEST_SEED, tmp_path,
                                     count_fixture(), horizon=8) for arm in study.ARMS]
    path = tmp_path/'raw'/f'R_{TEST_SEED}.npz'
    with np.load(path, allow_pickle=False) as saved:
        data = {k: saved[k] for k in saved.files}
    if corrupt == 'late_score':
        data['scores'][1, 4, 0] += 1
    else:
        data['counters'][4, -1] += 1
    np.savez_compressed(path, **data)
    episodes[-1]['raw'] = study.identity(path)  # Corruption is intentionally inside trusted fixture bytes.
    config = dict(seeds=[TEST_SEED], arms=list(study.ARMS), horizon=8,
                  orders=[list(o) for o in study.ORDERS], started_fits=0, optimizer_calls=0, training_labels=0)
    study.write_json(tmp_path/'config.json', config)
    study.write_json(tmp_path/'worker-status.json', dict(status='complete', episodes=episodes))
    monkeypatch.setattr(reader, 'SEEDS', (TEST_SEED,))
    monkeypatch.setattr(reader, 'HORIZON', 8)
    original = reader.read_episode
    def read_fixture(data, *, progress=None):
        return original(data, horizon=8, verify_seed=False, progress=progress)
    monkeypatch.setattr(reader, 'read_episode', read_fixture)
    monkeypatch.setattr(sys, 'argv', ['reader', '--out', str(tmp_path)])
    with pytest.raises(ValueError, match='scores|worker counter'):
        reader.main()
    status = json.loads((tmp_path/'reader-status.json').read_text())
    progress = status['progress']
    assert status['status'] == 'failed' and progress['status'] == 'incomplete'
    assert progress['episodes_completed'] == 2 and progress['episodes_started'] == 3
    assert progress['completed_episode_keys'] == [dict(arm=a, seed=TEST_SEED) for a in ('C', 'V')]
    current, counts = progress['current'], progress['counts']
    assert current['arm'] == 'R' and current['seed'] == TEST_SEED
    assert (current['tick'], current['actor'], current['stage']) == (
        (4, 4, 'saved_score_checks') if corrupt == 'late_score' else (8, None, 'counter_audit'))
    assert counts['score_requests_completed'] == counts['score_requests_attempted'] == 50
    assert counts['logical_model_ticks_completed'] == 5400
    assert counts['native_reconstructions_completed'] == (23 if corrupt == 'late_score' else 27)
    assert counts['native_dense_power_slots_completed'] == counts['native_reconstructions_completed']*275
    assert counts['controller_power_values_completed'] > 0
    assert counts['controller_power_values_completed'] == counts['controller_power_values_attempted']
    assert status['telemetry']['wall_seconds'] > 0 and status['telemetry']['process_cpu_seconds'] > 0
    assert not (tmp_path/'reading.json').exists() and not (tmp_path/'summary.json').exists()


def test_attempted_work_distinct_from_completed_on_internal_failure(monkeypatch):
    progress = reader.new_progress()
    own, users, sinr, peers = reader.decode(row(0, peers=((600., 450., 80.),)))
    prepared = reader.prepare_score(own, users, sinr, peers, progress=progress)
    assert progress['counts']['controller_power_values_completed'] == 110
    def fail_power(*args, **kwargs):
        raise RuntimeError('fixture power failure')
    monkeypatch.setattr(reader, 'local_power', fail_power)
    with pytest.raises(RuntimeError, match='power failure'):
        reader.ranking(prepared, np.array(((30., 0., 0.),)), 1, 0, progress=progress)
    assert progress['counts']['score_requests_attempted'] == 1
    assert progress['counts']['score_requests_completed'] == 0
    assert progress['counts']['logical_model_ticks_attempted'] == 108
    assert progress['counts']['logical_model_ticks_completed'] == 0


def test_failed_power_and_native_batches_preserve_attempts(monkeypatch):
    progress = reader.new_progress()
    def fail_log(*args, **kwargs):
        raise RuntimeError('fixture arithmetic failure')
    monkeypatch.setattr(reader.np, 'log10', fail_log)
    with pytest.raises(RuntimeError, match='arithmetic failure'):
        reader.local_power(np.array(((400., 400., 80.),)), np.array(((300., 300.),)), progress=progress)
    counts = progress['counts']
    assert counts['controller_power_batches_attempted'] == 1 and counts['controller_power_batches_completed'] == 0
    assert counts['controller_power_values_attempted'] == 1 and counts['controller_power_values_completed'] == 0
    positions, users = fixture_geometry()
    with pytest.raises(RuntimeError, match='arithmetic failure'):
        reader.native_radio(positions, users, 0, progress=progress)
    assert counts['native_reconstructions_attempted'] == 1 and counts['native_reconstructions_completed'] == 0
    assert counts['native_dense_power_slots_attempted'] == 275 and counts['native_dense_power_slots_completed'] == 0


def test_admitted_runner_retains_failed_reader_progress_without_summary(tmp_path, monkeypatch):
    """Mock inventory bookkeeping only; no model/native transitions or selected geometry."""
    import json
    from types import SimpleNamespace
    from experiments.candidates.uav_local_peer_forecast import run
    import scripts.hmasd_admission as admission
    monkeypatch.setattr(admission, 'require_admission', lambda *a, **k: {'sha': '0'*40})
    monkeypatch.setattr(study, 'source_binding', lambda sha: [])
    base = SimpleNamespace(n_uavs=5, n_users=50, max_steps=256, area_size=1000,
        height_range=(50, 150), max_speed=30, time_step=1., tx_power=23, noise_power=-80,
        min_sinr=3, max_connections=10, carrier_frequency=2e9, channel_model='free_space',
        use_shadowing=False, use_fdma=False, paper_reward=False, enable_transmitter_mask=False,
        transmitter_mask=np.ones(5, dtype=bool))
    monkeypatch.setattr(study, 'make_real', lambda seed: SimpleNamespace(env=base, close=lambda: None))
    def fake_collect(env, arm, seed, out, counts):
        counts['complete_episodes'] += 1
        counts['native_steps'] += 256
        counts['actor_ingests'] += 1280
        counts['rankings'] += 320
        return dict(arm=arm, seed=seed, controller_counts=dict(model_ticks=34560, shadow_decisions=0,
                    link_evaluations=0))
    monkeypatch.setattr(study, 'collect_episode', fake_collect)
    def fail_read(out, config, episodes, *, progress):
        progress['episodes_started'] = 3
        progress['episodes_completed'] = 2
        progress['counts']['score_requests_completed'] = 5
        progress['current'] = dict(arm='fixture', seed=TEST_SEED, tick=4, actor=2, stage='counter_audit')
        raise ValueError('fixture reader failure')
    monkeypatch.setattr(reader, 'read_panel', fail_read)
    monkeypatch.setattr(sys, 'argv', ['run.py', '--launch-sha', '0'*40, '--out', str(tmp_path)])
    with pytest.raises(ValueError, match='fixture reader failure'):
        run.main()
    status = json.loads((tmp_path/'reader-status.json').read_text())
    assert status['status'] == 'failed' and status['progress']['status'] == 'incomplete'
    assert status['progress']['counts']['score_requests_completed'] == 5
    assert status['progress']['current']['seed'] == TEST_SEED
    assert json.loads((tmp_path/'worker-status.json').read_text())['status'] == 'complete'
    assert json.loads((tmp_path/'terminal-status.json').read_text())['status'] == 'failed'
    assert not (tmp_path/'summary.json').exists() and not (tmp_path/'reading.json').exists()
