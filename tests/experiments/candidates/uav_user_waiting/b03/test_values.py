"""Synthetic legal-state/value checks: no native environment or radio calls."""

import json
import random

import numpy as np
import pytest
import torch

from experiments.candidates.uav_user_waiting.b03 import features as f
from experiments.candidates.uav_user_waiting.b03 import learner as l


def boundary(tick=8):
    last = np.full(50, -1, np.int64)
    age = np.zeros(50, np.int64)
    maximum = age.copy()
    windows = np.zeros((4, 50), bool)
    for t in range(tick):
        contacts = np.zeros(50, bool)
        if t in (0, 3, 6, 7):
            i = (0, 3, 6, 7).index(t)
            contacts[i * 10:(i + 1) * 10] = True
        age = np.where(contacts, 0, age + 1)
        maximum = np.maximum(maximum, age)
        last[contacts] = t
        windows[t // 64, contacts] = True
    return dict(sites=np.column_stack((np.arange(50) * 19, np.arange(50)[::-1] * 17)),
                positions=np.array([[100, 100, 50], [300, 400, 80], [500, 500, 100],
                                    [700, 700, 120], [900, 900, 150]]),
                commands=np.array([[1, 0, -1], [0, 1, 0], [-1, -1, 1], [0, 0, 0], [1, 1, 1]]),
                mask=21, previous_nav=np.arange(5), last=last, maximum=maximum,
                windows=windows, tick=tick, history_start=0, history_after=tick)


def scalar_basis(state):
    t = state['tick']
    ages = [0 if t == 0 else t - 1 - int(v) for v in state['last']]
    a = np.array(ages) / 256.
    m = state['maximum'] / 256.
    slack = m - a
    d = []
    for x, y in state['sites'][:, :2]:
        distances = []
        for i, (px, py, pz) in enumerate(state['positions']):
            if state['mask'] & (1 << i):
                distances.append(((px - x)**2 + (py - y)**2 + pz**2)**.5)
        d.append(min(distances) / (1000**2 + 1000**2 + 150**2)**.5)
    d = np.array(d)
    nav = np.zeros((5, 10))
    for i, v in enumerate(state['previous_nav']):
        nav[i, int(v)] = 1
    member = np.zeros(5)
    member[(t // 4) % 5] = 1
    relations = [[d[i], d[i]**2, slack[i], d[i]*a[i], d[i]*slack[i]] for i in range(50)]
    pooled = [a.mean(), (a*a).mean(), m.mean(), (m*m).mean(), slack.mean(), (slack*slack).mean(),
              d.mean(), (d*d).mean(), (d*a).mean(), (d*slack).mean()]
    blocks = [state['sites'][:, :2] / 1000., (state['positions'] - [0, 0, 50]) / [1000, 1000, 100],
              state['commands'], [bool(state['mask'] & (1 << i)) for i in range(5)], nav,
              a, m, state['windows'], state['last'] < 0, [1, 1, 1],
              [t / 256., (256 - t) / 256.], member, relations, pooled]
    return np.concatenate([np.asarray(v).reshape(-1) for v in blocks]).astype(np.float32)


def rows():
    X = np.zeros((5, 805), np.float32)
    X[:, :3] = np.array([[0, 1, 2], [1, 0, 1], [2, 1, 0], [-1, 2, 1], [1, 3, 2]]) / 4
    return X, np.array([0., 64., 128., 192., 256.]), np.array([11, 22, 22, 22, 33])


@pytest.mark.parametrize('tick', [0, 8, 64, 68, 256])
def test_exact_805_basis_matches_scalar_formula(tick):
    state = boundary(tick)
    value = f.pack_features(**state)
    assert value.shape == (805,) and value.dtype == np.float32
    np.testing.assert_array_equal(value, scalar_basis(state))
    assert f.FEATURE_SLICES['pooled'].stop == 805
    json.dumps(f.FEATURE_SPEC)
    state['sites'] = np.column_stack((state['sites'], np.full(50, 73)))
    np.testing.assert_array_equal(f.pack_features(**state), value)


def test_geometry_active_mask_and_age_interactions():
    state = boundary()
    before = f.pack_features(**state)
    state['positions'][1] = [1000, 0, 50]  # inactive member changes only its anchor block
    after = f.pack_features(**state)
    np.testing.assert_array_equal(after[f.FEATURE_SLICES['relations']], before[f.FEATURE_SLICES['relations']])
    state['positions'][0] = [0, 833, 50]
    changed = f.pack_features(**state)[f.FEATURE_SLICES['relations']].reshape(50, 5)
    assert not np.array_equal(changed[:, 0], before[f.FEATURE_SLICES['relations']].reshape(50, 5)[:, 0])
    age = (7 - state['last']) / 256.
    slack = state['maximum'] / 256. - age
    np.testing.assert_allclose(changed[:, 3], changed[:, 0] * age, rtol=1e-7, atol=1e-9)
    np.testing.assert_allclose(changed[:, 4], changed[:, 0] * slack, rtol=1e-7, atol=1e-9)


@pytest.mark.parametrize('change', [
    {'history_start': 4}, {'history_start': None}, {'history_after': 4}, {'tick': 9},
    {'mask': 0}, {'mask': True}, {'previous_nav': np.full(5, 10)},
    {'last': np.full(50, 8)}, {'last': np.full(50, -2)}, {'last': np.zeros(50)},
    {'maximum': np.zeros(50, int)}, {'maximum': np.full(50, 9)},
    {'windows': np.ones((4, 50), bool)}, {'windows': np.zeros((4, 50), int)},
    {'positions': np.full((5, 3), 50.5)}, {'commands': np.full((5, 3), 2)},
])
def test_unavailable_or_malformed_history_rejected(change):
    state = boundary()
    state.update(change)
    with pytest.raises(ValueError):
        f.pack_features(**state)


def test_equal_episode_weights_and_unregularized_intercept():
    X = np.zeros((4, 805), np.float32)
    model, stats, trace = l.fit_ridge(X, [0, 256, 256, 256], [0, 1, 1, 1])
    assert model.intercept == pytest.approx(.5)
    np.testing.assert_array_equal(model.coefficients, np.zeros(805))
    np.testing.assert_allclose(trace['row_weights'], [.5, 1/6, 1/6, 1/6])
    assert stats['final_weighted_mse'] == pytest.approx(.25)
    assert stats['final_prediction_rows'] == 4 and stats['initial_prediction_rows'] == 0
    np.testing.assert_allclose(trace['final_prediction'], .5)
    assert stats['analytic_solves'] == 1
    json.dumps(stats)


def test_ridge_float64_objective_matches_independent_two_parameter_solve():
    X, y, ids = rows()
    X[:, 1:] = 0
    model, stats, trace = l.fit_ridge(X, y, ids)
    w = np.array([1/3, 1/9, 1/9, 1/9, 1/3])
    D = np.column_stack((np.ones(5), X[:, 0].astype(np.float64)))
    gram = D.T @ (w[:, None] * D) + np.diag([0, .001])
    expected = np.linalg.solve(gram, D.T @ (w * y / 256))
    np.testing.assert_allclose([model.intercept, model.coefficients[0]], expected, rtol=1e-12)
    assert model.coefficients.dtype == np.float64
    predicted = D @ expected
    objective = np.dot(w, (predicted - y/256)**2) + .001 * expected[1]**2
    assert stats['final_objective'] == pytest.approx(objective, abs=1e-14)
    assert trace['gradient_norm'][0] < 1e-12
    np.testing.assert_allclose(trace['final_prediction'], predicted, rtol=1e-12)


def test_raw_clipping_and_terminal_does_not_call_model(monkeypatch):
    model = l.ValueModel('ridge', intercept=2)
    x = np.zeros(805, np.float32)
    assert model.raw_ticks(x) == 512
    np.testing.assert_array_equal(model.raw_ticks(np.stack((x, x))), [512, 512])
    assert model.evaluate(x, 252) == (512., 4.)
    model.intercept = -.5
    assert model.evaluate(x, 0) == (-128., 0.)
    monkeypatch.setattr(model, 'raw_ticks', lambda x: pytest.fail('terminal must not invoke inference'))
    assert model.evaluate(None, 256) == (0., 0.)
    with pytest.raises(ValueError):
        model.evaluate(x, 257)
    with pytest.raises(ValueError):
        l.ValueModel('ridge').raw_ticks(x.astype(np.float64))


def test_initial_neural_zero_head_ordinary_hidden_and_global_rng_isolation():
    before = torch.get_rng_state().clone()
    model = l.initial_neural_model()
    assert torch.equal(torch.get_rng_state(), before)
    arrays = model.arrays()
    assert sum(v.size for v in arrays.values()) == 119809
    assert np.count_nonzero(arrays['0.weight']) and np.count_nonzero(arrays['2.weight'])
    assert np.count_nonzero(arrays['4.weight']) == np.count_nonzero(arrays['4.bias']) == 0
    np.testing.assert_array_equal(model.raw_ticks(rows()[0]), np.zeros(5, np.float32))
    assert all(p.grad is None for p in model.network.parameters())
    arrays['0.weight'][:] = 0
    assert np.count_nonzero(model.arrays()['0.weight'])


def test_neural_seed_sampling_exact_updates_replay_and_rng_isolation():
    X, y, ids = rows()
    torch_state = torch.get_rng_state().clone()
    numpy_state = np.random.get_state()
    python_state = random.getstate()
    model, stats, trace = l.fit_neural(X, y, ids, updates=3, batch_size=4)
    assert torch.equal(torch.get_rng_state(), torch_state)
    now_numpy = np.random.get_state()
    assert numpy_state[0] == now_numpy[0] and numpy_state[2:] == now_numpy[2:]
    np.testing.assert_array_equal(numpy_state[1], now_numpy[1])
    assert random.getstate() == python_state
    replay, replay_stats, replay_trace = l.fit_neural(X, y, ids, updates=3, batch_size=4)
    for name, value in model.arrays().items():
        np.testing.assert_array_equal(value, replay.arrays()[name])
    for name, value in trace.items():
        np.testing.assert_array_equal(value, replay_trace[name])
    rng = np.random.Generator(np.random.PCG64(l.SAMPLE_SEED))
    groups = [np.flatnonzero(ids == i) for i in np.unique(ids)]
    expected = np.empty((3, 4), int)
    for i in range(3):
        for j in range(4):
            group = groups[int(rng.integers(3))]
            expected[i, j] = group[int(rng.integers(len(group)))]
    np.testing.assert_array_equal(trace['sampled_rows'], expected)
    assert stats['optimizer_updates'] == 3 and stats['minibatch_presentations'] == 12
    assert stats['final_prediction_rows'] == 5 and stats['initial_prediction_rows'] == 0
    assert np.all(trace['gradient_norm'] > 0) and np.all(trace['parameter_change_l2'] > 0)
    assert stats['parameter_movement_l2'] > 0
    np.testing.assert_array_equal(trace['final_prediction'], model.raw_ticks(X) / 256)
    assert all(p.grad is None for p in model.network.parameters())
    json.dumps(stats)
    assert replay_stats['final_sha256'] == stats['final_sha256']


def test_first_neural_step_matches_independent_adam_and_zero_head_gradient():
    X, y, ids = rows()
    model, stats, trace = l.fit_neural(X, y, ids, updates=1, batch_size=4)
    reference = l.initial_neural_model()
    hidden = {k: v for k, v in reference.arrays().items() if k.startswith(('0.', '2.'))}
    optimizer = torch.optim.Adam(reference.network.parameters(), lr=.001, betas=(.9, .999), eps=1e-8, weight_decay=0)
    idx = trace['sampled_rows'][0]
    prediction = reference.network(torch.from_numpy(X[idx])).squeeze(-1)
    loss = (prediction - torch.from_numpy((y[idx] / 256).astype(np.float32))).square().mean()
    loss.backward()
    optimizer.step()
    for name, value in model.arrays().items():
        np.testing.assert_array_equal(value, reference.arrays()[name])
    for name, value in hidden.items():
        np.testing.assert_array_equal(value, model.arrays()[name])
    assert np.count_nonzero(model.arrays()['4.weight']) > 0
    assert trace['loss'][0] == float(loss.detach())


@pytest.mark.parametrize('kind', ['ridge', 'neural'])
def test_pickle_free_checkpoint_exact_roundtrip_and_digest(kind, tmp_path):
    X, y, ids = rows()
    if kind == 'ridge':
        model, _, _ = l.fit_ridge(X, y, ids)
    else:
        model, _, _ = l.fit_neural(X, y, ids, updates=2, batch_size=4)
    path = tmp_path / 'checkpoint.bin'
    l.save_model(path, model)
    with np.load(path, allow_pickle=False) as data:
        payload = {name: data[name] for name in data.files}
        assert all(value.dtype.kind != 'O' for value in payload.values())
    before = torch.get_rng_state().clone()
    restored = l.load_model(path)
    assert torch.equal(torch.get_rng_state(), before)
    assert restored.parameter_sha256() == model.parameter_sha256()
    for name, array in model.arrays().items():
        np.testing.assert_array_equal(restored.arrays()[name], array)
    np.testing.assert_array_equal(restored.raw_ticks(X), model.raw_ticks(X))
    payload['parameter_sha256'] = np.array('bad')
    with path.open('wb') as stream:
        np.savez(stream, **payload)
    with pytest.raises(ValueError, match='digest'):
        l.load_model(path)
