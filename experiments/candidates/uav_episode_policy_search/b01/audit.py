"""One full saved-data replay: scalar physics and independent policy laws."""
import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, initial_nav
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from .contract import NEURAL, LEARNERS, array_digest
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.environment import original_layout
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.physics import assert_radio_equal, scalar_state
from .reading import episode_metrics


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def equal(actual, expected, message, tolerance=None):
    a, b = np.asarray(actual), np.asarray(expected)
    require(a.shape == b.shape, message + ': shape')
    if tolerance is None:
        require(np.array_equal(a, b), message)
    else:
        require(np.isfinite(a).all() and np.isfinite(b).all()
                and np.allclose(a, b, atol=tolerance, rtol=0.), message)


def _gate_vector(answer, kind):
    features = np.asarray(answer['features'])
    count = min(sum(float(features[3 + 3 * i + 2]) > 0 for i in range(20)), 10)
    onehot = np.array([float(i == count) for i in range(11)], dtype=np.float64)
    raw = np.r_[features.astype(np.float64), onehot]
    return (raw if kind == 'RAW' else np.r_[raw, answer['hidden'].astype(np.float64)]), count


def _schema(raw, horizon, parent, learner=False):
    d = horizon // 4
    shapes = dict(positions=(horizon + 1, 5, 3), observations=(horizon, 5, 104), commands=(horizon, 5, 3),
                  reward=(horizon,), served=(horizon,), sinr_quality=(horizon,), sinr=(horizon, 5, 50),
                  peer_sinr=(horizon, 5, 5), connections=(horizon, 5, 50), transmitter_mask=(horizon, 5),
                  terminated=(horizon,), truncated=(horizon,), step_generation=(horizon,), step_path_loss_misses=(horizon,),
                  nav_pre=(d, 5), nav_next=(d, 5), fallback=(d, 5), action_index=(d, 5), memo_hit=(d, 5),
                  features=(d, 5, 114), n_current=(d, 5), n_peers=(d, 5), probabilities=(d, 5, 27),
                  innovation=(d, 5), entropy=(d, 5), old_decision_mask=(d, 5), installed_mask=(d, 5),
                  refresh_sinr=(d, 5, 50), refresh_peer_sinr=(d, 5, 5), refresh_connections=(d, 5, 50),
                  refresh_observations=(d, 5, 104), initial_users=(50, 2), initial_sinr=(5, 50),
                  initial_peer_sinr=(5, 5), initial_connections=(5, 50), initial_generation=(),
                  terminal_observation=(5, 104), decision_ticks=(d,))
    for key in ('eligible_agent', 'gate_count', 'gate_innovation', 'gate_prediction', 'gate_requested_off',
                'gate_off', 'gate_forced', 'refresh_generation', 'refresh_path_loss_misses'):
        shapes[key] = (d,)
    if parent in NEURAL:
        shapes.update(logits=(d, 5, 27), hidden=(d, 5, 128))
    if learner:
        shapes.update(head_logits=(d,5,27), p0_probabilities=(d,5,27), p0_action_index=(d,5), zero_head_error=(d,5))
    if parent not in ('P0', 'Bstar0'):
        shapes.update(policy_scores=(d, 5, 27), policy_served=(d, 5, 27), c_index=(d, 5))
    if parent == 'Hdirect':
        shapes['parent_probabilities'] = (d, 5, 27)
    require(set(raw) == set(shapes), 'complete raw field roster')
    booleans = {'connections', 'transmitter_mask', 'terminated', 'truncated', 'fallback', 'memo_hit',
                'old_decision_mask', 'installed_mask', 'gate_requested_off', 'gate_off', 'gate_forced',
                'refresh_connections', 'initial_connections'}
    integers = {'served', 'step_generation', 'step_path_loss_misses', 'nav_pre', 'nav_next', 'action_index',
                'n_current', 'n_peers', 'eligible_agent', 'gate_count', 'refresh_generation', 'refresh_path_loss_misses',
                'initial_generation', 'decision_ticks', 'c_index', 'p0_action_index'}
    fp32 = {'observations', 'commands', 'features', 'refresh_observations', 'terminal_observation', 'logits', 'hidden'}
    for key, shape in shapes.items():
        value = raw[key]
        require(value.shape == shape, key + ': raw shape')
        expected_dtype = np.bool_ if key in booleans else np.int64 if key in integers else np.float32 if key in fp32 else np.float64
        require(value.dtype == expected_dtype, key + ': raw dtype')
        if 'sinr' not in key or key == 'sinr_quality':
            require(np.isfinite(value).all(), key + ': nonfinite value')
    equal(raw['decision_ticks'], np.arange(0, horizon, 4), 'complete decision clocks')


def _radio(raw, prefix, index, state, maxima):
    for key in ('sinr', 'peer_sinr'):
        stored = raw[prefix + key] if index is None else raw[prefix + key][index]
        maxima['radio'] = max(maxima['radio'], assert_radio_equal(stored, state[key]))
    stored = raw[prefix + 'connections'] if index is None else raw[prefix + 'connections'][index]
    equal(stored, state['connections'], prefix + 'greedy capacity assignment')


def audit_episode(raw, row, protocol, actor, *, theta=None, counts=None, inflight=None):
    # Importing the reference here lets scalar-only tests avoid loading torch.
    from .reference import ReferencePolicy
    counts = {} if counts is None else counts
    parent, gate = row['parent'], row['gate']
    learner = row['program'] in LEARNERS
    _schema(raw, protocol.horizon, parent, learner)
    world, horizon = row['world'], protocol.horizon
    positions, users = original_layout(world)
    equal(raw['positions'][0], positions, 'original five-agent reset positions')
    equal(raw['initial_users'], users, 'original user reset positions')
    require(row['initial_state_sha256'] == array_digest(positions, users), 'initial state digest')
    initial_generation = int(raw['initial_generation'])
    equal(raw['step_generation'], initial_generation + np.arange(1, horizon + 1), 'one physical generation per native tick')
    equal(raw['refresh_generation'], initial_generation + np.arange(0, horizon, 4), 'setter reuses physical generation')
    equal(raw['step_path_loss_misses'], np.full(horizon, 260), 'native vector cache-miss slot counter')
    equal(raw['refresh_path_loss_misses'], np.zeros(horizon // 4, dtype=int), 'no setter distance recomputation')
    equal(raw['terminated'], np.arange(horizon) == horizon - 1, 'terminal clock')
    equal(raw['truncated'], np.zeros(horizon, dtype=bool), 'no truncation')
    maxima = dict(radio=0., observation=0., reward=0., prediction=0.)
    mask = np.ones(5, dtype=bool)
    state = scalar_state(positions, users, mask, 0, horizon, counts=counts)
    _radio(raw, 'initial_', None, state, maxima)
    navs = [initial_nav(raw['observations'][0, agent]) for agent in range(5)]
    policies = [ReferencePolicy(parent, actor, world=world, agent=agent, sampling_root=row['motion_root'], family=row['family'] if learner else None, theta=theta, zero_check=row['zero_check']) for agent in range(5)]
    if inflight is not None:
        inflight.update(id=row['id'], parent=parent, policy_agents=[policy.counters for policy in policies])
    for tick in range(horizon):
        if inflight is not None:
            inflight['tick'] = tick
        equal(raw['observations'][tick], state['observations'], 'saved old returned observation', tolerance=1e-7)
        maxima['observation'] = max(maxima['observation'], float(np.max(np.abs(raw['observations'][tick] - state['observations']))))
        if tick % 4 == 0:
            di, agent = tick // 4, (tick // 4) % 5
            equal(raw['old_decision_mask'][di], mask, 'decision uses previous applied mask')
            equal(raw['nav_pre'][di], navs, 'private navigation recurrence')
            equal(raw['eligible_agent'][di], agent, 'rotating eligibility')
            answers = []
            for i, policy in enumerate(policies):
                answer = policy.query(raw['observations'][tick, i].copy(), tick, int(navs[i]))
                answers.append(answer)
                navs[i] = answer['next_nav']
                for field in ('features', 'fallback', 'action_index', 'memo_hit', 'n_current', 'n_peers', 'innovation'):
                    equal(raw[field][di, i], answer[field], 'motion ' + field)
                for field in ('probabilities', 'entropy'):
                    equal(raw[field][di, i], answer[field], 'motion ' + field, tolerance=5e-14)
                if learner:
                    equal(raw['zero_head_error'][di,i], answer['zero_head_error'], 'zero head identity error')
                    for field in ('head_logits', 'p0_probabilities'):
                        equal(raw[field][di,i], answer[field], 'independent head ' + field, tolerance=5e-14)
                    equal(raw['p0_action_index'][di,i], answer['p0_action_index'], 'same innovation P0 choice')
                if parent in NEURAL:
                    for field in ('logits', 'hidden'):
                        equal(raw[field][di, i], answer[field], 'original paid forward ' + field)
                if parent not in ('P0', 'Bstar0'):
                    equal(raw['policy_scores'][di, i], answer['scores'], 'complete C scores', tolerance=1e-12)
                    equal(raw['policy_served'][di, i], answer['served'], 'complete C service')
                    equal(raw['c_index'][di, i], answer['c_index'], 'C anchor')
                if parent == 'Hdirect':
                    equal(raw['parent_probabilities'][di, i], answer['parent_probabilities'], 'H parent law', tolerance=5e-14)
                expected_command = COMMANDS[answer['action_index']]
                equal(raw['commands'][tick:tick + 4, i], np.tile(expected_command, (4, 1)), 'four held original motion commands')
            equal(raw['nav_next'][di], navs, 'navigation update')
            _, count = _gate_vector(answers[agent], 'RAW')
            require(gate in ('A', 'ZERO'), 'declared transmitter rights')
            executed = gate == 'ZERO' and count == 0
            for key, value in (('gate_count', count), ('gate_innovation', -1.), ('gate_requested_off', executed),
                               ('gate_off', executed), ('gate_forced', False), ('gate_prediction', 0.)):
                equal(raw[key][di], value, 'gate law ' + key)
            mask = np.ones(5, dtype=bool)
            mask[agent] = not executed
            equal(raw['installed_mask'][di], mask, 'one eligible gate bit')
            refreshed = scalar_state(positions, users, mask, tick, horizon, counts=counts)
            _radio(raw, 'refresh_', di, refreshed, maxima)
            equal(raw['refresh_observations'][di], refreshed['observations'], 'saved setter row', tolerance=1e-7)
            maxima['observation'] = max(maxima['observation'], float(np.max(np.abs(
                raw['refresh_observations'][di] - refreshed['observations']))))
        equal(raw['transmitter_mask'][tick], mask, 'four held mask ticks')
        positions = np.clip(positions + raw['commands'][tick].astype(np.float64) * 30., [0., 0., 50.], [1000., 1000., 150.])
        equal(raw['positions'][tick + 1], positions, 'held native motion including silent UAVs')
        state = scalar_state(positions, users, mask, tick + 1, horizon, counts=counts)
        _radio(raw, '', tick, state, maxima)
        equal(raw['served'][tick], state['served'], 'native total served')
        for key in ('reward', 'sinr_quality'):
            equal(raw[key][tick], state[key], 'native ' + key, tolerance=2e-13)
            maxima['reward'] = max(maxima['reward'], abs(float(raw[key][tick]) - state[key]))
    equal(raw['terminal_observation'], state['observations'], 'terminal local rows', tolerance=1e-7)
    maxima['observation'] = max(maxima['observation'], float(np.max(np.abs(
        raw['terminal_observation'] - state['observations']))))
    for key, value in episode_metrics(raw).items():
        equal(row[key], value, 'episode metric ' + key, tolerance=1e-12 if type(value) is float else None)
    policy_counts = sum_counts(policy.counters for policy in policies)
    require(policy_counts == row['policy_counts'], 'complete original policy/cache/work counts')
    counts['saved_episodes'] = counts.get('saved_episodes', 0) + 1
    counts['saved_native_ticks'] = counts.get('saved_native_ticks', 0) + horizon
    counts['policy_requests'] = counts.get('policy_requests', 0) + horizon // 4 * 5
    counts['gate_requests'] = counts.get('gate_requests', 0) + horizon // 4
    if inflight is not None:
        inflight.clear()
    return dict(max_abs_errors=maxima, policy_counts=policy_counts)
