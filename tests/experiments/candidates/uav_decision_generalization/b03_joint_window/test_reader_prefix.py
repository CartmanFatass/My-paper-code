"""Read-only recovery identity and exact motion checks; no native/model calls."""
import copy
import json
import numpy as np
import pytest

from experiments.candidates.uav_decision_generalization.b03_joint_window import contract as c
from experiments.candidates.uav_decision_generalization.b03_joint_window import evidence as e
from experiments.candidates.uav_decision_generalization.b03_joint_window import independent as r
from experiments.candidates.uav_decision_generalization.b03_joint_window import reader_prefix as p


def test_norm_receives_independent_copied_vectors(monkeypatch):
    # The saved failure vector sits near the exact >1 branch. Distinct aligned
    # copies, rather than a tolerance, reproduce the host's arithmetic path.
    raw = np.tile([.6478229245445858, -.7603696056554017, .04651366713073793], (2, 6, 1))
    expected = raw.copy()
    for x in expected.reshape(-1, 3):
        value = x.copy()
        norm = float(np.linalg.norm(value))
        if norm > 1:
            x[:] = value / norm
    native_norm = np.linalg.norm
    observed = []
    def norm(value):
        observed.append(value.base is None and value.flags.owndata)
        return native_norm(value)
    monkeypatch.setattr(np.linalg, 'norm', norm)
    actual, events = r.clipped_actions(raw)
    assert len(observed) == 12 and all(observed)
    assert np.array_equal(actual, expected)
    assert not events.any()
    bad = actual.copy()
    bad[0, 0, 0] = np.nextafter(bad[0, 0, 0], np.inf)
    with pytest.raises(AssertionError):
        r.same(bad, actual, 'no new ULP tolerance')


def prefix_fixture(tmp_path):
    old = {p.PREFIX + 'run.py': 'old-entry', p.PREFIX + 'independent.py': 'old-reader', 'host.py': 'fixed'}
    new = {**old, p.PREFIX + 'run.py': 'new-entry', p.PREFIX + 'independent.py': 'new-reader', p.PREFIX + 'reader_prefix.py': 'new-prefix'}
    config = {'source_sha256': old, 'mode': 'reader', 'contract': {},
              'worker_input': {'sha256': 'worker-locator'}, 'launch_sha': 'old-reader-commit'}
    summary = {'launch_sha': 'old-reader-commit', 'status': 'FAILED',
               'error': {'type': 'AssertionError', 'message': 'dtype-preserving unit-ball clip: maximum absolute error 2.220446049250313e-16'},
               'training_rollouts_checked': 135, 'frozen_checked': 167,
               'inflight': {'kind': 'frozen', 'programme': 'O', 'world': 109220001, 'phase': 'main'},
               'cost': {'prior': {'prior_counts': {'native_steps': 1196000}}, 'counts': {'reader_model_team_steps': 83000},
                        'resources': {'cumulative_cpu_seconds': 52308.}}}
    for name, value in (('config', config), ('summary', summary), ('process-exit', {'exit_code': 1})):
        e.write_json(tmp_path / (name + '.json'), value)
    manifest = {'training': [{'arm': arm, 'rollout': roll} for arm in c.ARMS for roll in range(1, 46)],
                'frozen': [{'programme': 'synthetic', 'world': world} for world in range(167)]}
    checks = {'training': [], 'frozen': []}
    for row in manifest['training']:
        file = tmp_path / f"checks/training/{row['arm']}_{row['rollout']:02}.json"
        e.write_json(file, row); checks['training'].append(e.identity(file, tmp_path))
    for row in manifest['frozen']:
        file = tmp_path / f"checks/frozen/{row['programme']}_{row['world']}.json"
        e.write_json(file, row); checks['frozen'].append(e.identity(file, tmp_path))
    locator = {'schema': 1, 'root': str(tmp_path), 'config_sha256': e.hash_file(tmp_path / 'config.json'),
               'summary_sha256': e.hash_file(tmp_path / 'summary.json'), 'exit_sha256': e.hash_file(tmp_path / 'process-exit.json'),
               'checks': checks, 'source_changes': p.source_delta(old, new)}
    context = {'worker_config': {'source_sha256': old, 'contract': {}}, 'source_sha256': new,
               'config': {'worker_input': {'sha256': 'worker-locator'}}, 'manifest': manifest}
    prior = {'prior_counts': {'native_steps': 1196000, 'reader_model_team_steps': 83000}, 'prior_cpu_seconds': 52309.}
    return locator, context, prior


def test_prefix_binds_full_roster_hashes_source_and_prior_cost(tmp_path):
    locator, context, prior = prefix_fixture(tmp_path)
    result = p.validate_prefix(locator, context, prior)
    assert len(result['training']) == 135 and len(result['frozen']) == 167
    for kind in ('source', 'roster', 'hash', 'cost'):
        loc, ctx, cost = copy.deepcopy((locator, context, prior))
        if kind == 'source':
            ctx['source_sha256']['host.py'] = 'changed-worker'
            loc['source_changes'] = p.source_delta(ctx['worker_config']['source_sha256'], ctx['source_sha256'])
        elif kind == 'roster':
            loc['checks']['frozen'].pop()
        elif kind == 'hash':
            loc['checks']['training'][0]['sha256'] = '0' * 64
        else:
            cost['prior_counts']['reader_model_team_steps'] = 82999
        with pytest.raises((ValueError, AssertionError)):
            p.validate_prefix(loc, ctx, cost)


@pytest.mark.parametrize('dtype', [np.float32, np.float64])
def test_recheck_counts_separately_and_rejects_any_changed_position(dtype):
    actions = np.zeros((2, 500, 6, 3), dtype=dtype)
    positions = np.zeros((2, 501, 6, 3), dtype=np.float64); positions[..., 2] = 100.
    raw = {'raw_actions': actions, 'executed_actions': actions.copy(), 'positions': positions,
           'action_clip_events': np.zeros((2, 500), dtype=np.int64)}
    meter = e.Meter({'schema': 1, 'prior_cpu_seconds': 0., 'prior_counts': {}})
    p.recheck_movement(raw, meter)
    assert meter.counts == {'reader_prefix_movement_recheck_uav_ticks': 6000}
    positions[0, 1, 0, 0] = np.nextafter(0., 1.)
    with pytest.raises(AssertionError):
        p.recheck_movement(raw, meter)
